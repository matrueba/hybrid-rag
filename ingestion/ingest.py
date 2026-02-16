
import os
import asyncio
import logging
import glob
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse
from dataclasses import dataclass
from supabase import create_client, Client
from dotenv import load_dotenv
from models.chuncker import ChunkingConfig, DocumentChunk
from chuncker import create_chunker
from models.ingest import IngestionConfig, IngestionResult


try:
    from embedder import create_embedder
except ImportError:
    try:
        from ingestion.embedder import create_embedder
    except ImportError:
        create_embedder = None

if not create_embedder:
    class MockEmbedder:
        async def embed_chunks(self, chunks):
            # Mock 1536 dim embeddings
            for chunk in chunks:
                chunk.embedding = [0.1] * 1536
            return chunks
    def create_embedder():
        return MockEmbedder()

try:
    from settings import load_settings
except ImportError:
    from ingestion.settings import load_settings

load_dotenv()

logger = logging.getLogger(__name__)



class DocumentIngestionPipeline:
    """Pipeline for ingesting documents into Supabase vector database."""

    def __init__(
        self,
        config: IngestionConfig,
        documents_folder: str = "documents",
        clean_before_ingest: bool = True,
        source_type: str = "local",
        gdrive_folder_id: str = ""
    ):
        """
        Initialize ingestion pipeline.

        Args:
            config: Ingestion configuration
            documents_folder: Folder containing documents
            clean_before_ingest: Whether to clean existing data before ingestion
            source_type: 'local' for local files, 'gdrive' for Google Drive
            gdrive_folder_id: Google Drive folder ID (required if source_type='gdrive')
        """
        self.config = config
        self.documents_folder = documents_folder
        self.clean_before_ingest = clean_before_ingest
        self.source_type = source_type
        self.gdrive_folder_id = gdrive_folder_id
        self._temp_dir = None  # Temp dir for Google Drive downloads
        self.settings = load_settings()
        self.supabase: Optional[Client] = None
        self.chunker_config = ChunkingConfig(
            max_tokens=config.max_tokens
        )
        self.chunker = create_chunker(self.chunker_config)
        self.embedder = create_embedder()
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize Supabase connection.

        Raises:
            Exception: If Supabase connection fails
        """
        if self._initialized:
            return

        logger.info("Initializing ingestion pipeline...")

        try:
            # Initialize Supabase client
            if not self.settings.supabase_url or not self.settings.supabase_key:
                 raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
            
            self.supabase = create_client(
                self.settings.supabase_url,
                self.settings.supabase_key
            )
            
            logger.info("Connected to Supabase")

        except Exception as e:
            logger.exception("supabase_connection_failed", error=str(e))
            raise

        self._initialized = True
        logger.info("Ingestion pipeline initialized")

    async def close(self) -> None:
        """Close connections."""
        if self._initialized:
            # Supabase interaction is HTTP stateless, but if we used a stateful client we would close it here.
            # verify if supabase-py needs closing. The python client is typically just a wrapper around httpx or similar.
            self.supabase = None
            self._initialized = False
            logger.info("Ingestion pipeline closed")

    def _find_document_files(self) -> List[str]:
        """
        Find all supported document files in the documents folder.

        Returns:
            List of file paths
        """
        if not os.path.exists(self.documents_folder):
            logger.error(f"Documents folder not found: {self.documents_folder}")
            return []

        # Supported file patterns - Docling + text formats + audio
        patterns = [
            "*.md", "*.markdown", "*.txt",  # Text formats
            "*.pdf",  # PDF
            "*.docx", "*.doc",  # Word
            "*.pptx", "*.ppt",  # PowerPoint
            "*.xlsx", "*.xls",  # Excel
            "*.html", "*.htm",  # HTML
            "*.mp3", "*.wav", "*.m4a", "*.flac",  # Audio formats
        ]
        files = []

        for pattern in patterns:
            files.extend(
                glob.glob(
                    os.path.join(self.documents_folder, "**", pattern),
                    recursive=True
                )
            )

        return sorted(files)

    def _read_document(self, file_path: str) -> tuple[str, Optional[Any]]:
        """
        Read document content from file - supports multiple formats via Docling.

        Args:
            file_path: Path to the document file

        Returns:
            Tuple of (markdown_content, docling_document).
            docling_document is None only for text files.
        """
        file_ext = os.path.splitext(file_path)[1].lower()

        # Audio formats - transcribe with Whisper ASR
        audio_formats = ['.mp3', '.wav', '.m4a', '.flac']
        if file_ext in audio_formats:
            # Returns tuple: (markdown_content, docling_document)
            return self._transcribe_audio(file_path)

        # Docling-supported formats (convert to markdown)
        docling_formats = [
            '.pdf', '.docx', '.doc', '.pptx', '.ppt',
            '.xlsx', '.xls', '.html', '.htm',
            '.md', '.markdown'  # Markdown files for HybridChunker
        ]

        if file_ext in docling_formats:
            try:
                from docling.document_converter import DocumentConverter

                logger.info(
                    f"Converting {file_ext} file using Docling: "
                    f"{os.path.basename(file_path)}"
                )

                converter = DocumentConverter()
                result = converter.convert(file_path)

                # Export to markdown for consistent processing
                markdown_content = result.document.export_to_markdown()
                logger.info(
                    f"Successfully converted {os.path.basename(file_path)} "
                    f"to markdown"
                )

                # Return both markdown and DoclingDocument for HybridChunker
                return (markdown_content, result.document)

            except Exception as e:
                logger.error(f"Failed to convert {file_path} with Docling: {e}")
                # Fall back to raw text if Docling fails
                logger.warning(f"Falling back to raw text extraction for {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return (f.read(), None)
                except Exception:
                    return (
                        f"[Error: Could not read file {os.path.basename(file_path)}]",
                        None
                    )

        # Text-based formats (read directly)
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return (f.read(), None)
            except UnicodeDecodeError:
                # Try with different encoding
                with open(file_path, 'r', encoding='latin-1') as f:
                    return (f.read(), None)

    def _transcribe_audio(self, file_path: str) -> tuple[str, Optional[Any]]:
        """
        Transcribe audio file using Whisper ASR via Docling.

        Args:
            file_path: Path to the audio file

        Returns:
            Tuple of (markdown_content, docling_document)
        """
        try:
            from pathlib import Path
            from docling.document_converter import (
                DocumentConverter,
                AudioFormatOption
            )
            from docling.datamodel.pipeline_options import AsrPipelineOptions
            from docling.datamodel import asr_model_specs
            from docling.datamodel.base_models import InputFormat
            from docling.pipeline.asr_pipeline import AsrPipeline

            # Use Path object - Docling expects this
            audio_path = Path(file_path).resolve()
            logger.info(
                f"Transcribing audio file using Whisper Turbo: {audio_path.name}"
            )

            # Verify file exists
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            # Configure ASR pipeline with Whisper Turbo model
            pipeline_options = AsrPipelineOptions()
            pipeline_options.asr_options = asr_model_specs.WHISPER_TURBO

            converter = DocumentConverter(
                format_options={
                    InputFormat.AUDIO: AudioFormatOption(
                        pipeline_cls=AsrPipeline,
                        pipeline_options=pipeline_options,
                    )
                }
            )

            # Transcribe the audio file
            result = converter.convert(audio_path)

            # Export to markdown with timestamps
            markdown_content = result.document.export_to_markdown()
            logger.info(f"Successfully transcribed {os.path.basename(file_path)}")

            # Return both markdown and DoclingDocument for HybridChunker
            return (markdown_content, result.document)

        except Exception as e:
            logger.error(f"Failed to transcribe {file_path} with Whisper ASR: {e}")
            return (
                f"[Error: Could not transcribe audio file "
                f"{os.path.basename(file_path)}]",
                None
            )

    def _extract_title(self, content: str, file_path: str) -> str:
        """
        Extract title from document content or filename.

        Args:
            content: Document content
            file_path: Path to the document file

        Returns:
            Document title
        """
        # Try to find markdown title
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()

        # Fallback to filename
        return os.path.splitext(os.path.basename(file_path))[0]

    def _extract_document_metadata(
        self,
        content: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from document content.

        Args:
            content: Document content
            file_path: Path to the document file

        Returns:
            Document metadata dictionary
        """
        metadata = {
            "file_path": file_path,
            "file_size": len(content),
            "ingestion_date": datetime.now().isoformat()
        }

        # Try to extract YAML frontmatter
        if content.startswith('---'):
            try:
                import yaml
                end_marker = content.find('\n---\n', 4)
                if end_marker != -1:
                    frontmatter = content[4:end_marker]
                    yaml_metadata = yaml.safe_load(frontmatter)
                    if isinstance(yaml_metadata, dict):
                        metadata.update(yaml_metadata)
            except ImportError:
                logger.warning(
                    "PyYAML not installed, skipping frontmatter extraction"
                )
            except Exception as e:
                logger.warning(f"Failed to parse frontmatter: {e}")

        # Extract some basic metadata from content
        lines = content.split('\n')
        metadata['line_count'] = len(lines)
        metadata['word_count'] = len(content.split())

        return metadata

    async def _save_to_supabase(
        self,
        title: str,
        source: str,
        content: str,
        chunks: List[DocumentChunk],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Save document and chunks to Supabase.

        Args:
            title: Document title
            source: Document source path
            content: Document content
            chunks: List of document chunks with embeddings
            metadata: Document metadata

        Returns:
            Document ID (UUID as string)

        Raises:
            Exception: If Supabase operations fail
        """
        
        # Insert document
        document_data = {
            "title": title,
            "source": source,
            "content": content,
            "metadata": metadata,
            # "created_at": datetime.now().isoformat() # Let Supabase handle defaults if possible, or send ISO
        }

        # Supabase-py synchronous/async usage depends on client. 
        # The standard 'supabase' package is sync mostly but can be used in async loop.
        # However, `create_client` returns a Sync client by default unless we use AsyncClient?
        # Standard supabase-py is sync. We should probably wrap it or use it synchronously.
        # Since this method is async, we can wrap sync calls in a thread executor if needed, 
        # but for now we'll just call it.
        
        # Note: supabase-py v2 syntax
        res = self.supabase.table(self.settings.documents_table).insert(document_data).execute()
        
        if not res.data:
            raise Exception("Failed to insert document")
            
        document_id = res.data[0]['id'] # Assuming ID is returned
        logger.info(f"Inserted document with ID: {document_id}")

        # Insert chunks
        chunk_dicts = []
        for chunk in chunks:
            chunk_dict = {
                "document_id": document_id,
                "content": chunk.content,
                "embedding": chunk.embedding,
                "chunk_index": chunk.index,
                "metadata": chunk.metadata,
                "token_count": chunk.token_count,
            }
            chunk_dicts.append(chunk_dict)

        if chunk_dicts:
             # Batch insert
            self.supabase.table(self.settings.chunks_table).insert(chunk_dicts).execute()
            logger.info(f"Inserted {len(chunk_dicts)} chunks")

        return str(document_id)

    async def _clean_databases(self) -> None:
        """Clean existing data from Supabase tables."""
        logger.warning("Cleaning existing data from Supabase...")

        # Delete all chunks first (to respect FK relationships if enforced)
        # Using .neq('id', 0000) is a hack to delete all rows if delete requires a filter
        # Or delete where chunk_index >= -1
        try:
             self.supabase.table(self.settings.chunks_table).delete().neq("chunk_index", -999).execute()
        except:
             pass # Maybe table empty

        # Delete all documents
        try:
            self.supabase.table(self.settings.documents_table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        except:
             pass

        logger.info("Cleaned Supabase tables")

    async def _ingest_single_document(self, file_path: str) -> IngestionResult:
        """
        Ingest a single document.

        Args:
            file_path: Path to the document file

        Returns:
            Ingestion result
        """
        start_time = datetime.now()

        # Read document (returns tuple: content, docling_doc)
        document_content, docling_doc = self._read_document(file_path)
        document_title = self._extract_title(document_content, file_path)
        document_source = os.path.relpath(file_path, self.documents_folder)

        # Extract metadata from content
        document_metadata = self._extract_document_metadata(
            document_content,
            file_path
        )

        logger.info(f"Processing document: {document_title}")

        # Chunk the document - pass DoclingDocument for HybridChunker
        chunks = await self.chunker.chunk_document(
            content=document_content,
            title=document_title,
            source=document_source,
            metadata=document_metadata,
            docling_doc=docling_doc  # Pass DoclingDocument for HybridChunker
        )

        if not chunks:
            logger.warning(f"No chunks created for {document_title}")
            return IngestionResult(
                document_id="",
                title=document_title,
                chunks_created=0,
                processing_time_ms=(
                    datetime.now() - start_time
                ).total_seconds() * 1000,
                errors=["No chunks created"]
            )

        logger.info(f"Created {len(chunks)} chunks")

        # Generate embeddings
        embedded_chunks = await self.embedder.embed_chunks(chunks)
        logger.info(f"Generated embeddings for {len(embedded_chunks)} chunks")

        # Save to Supabase
        document_id = await self._save_to_supabase(
            document_title,
            document_source,
            document_content,
            embedded_chunks,
            document_metadata
        )
        
        # Calculate processing time
        processing_time = (
            datetime.now() - start_time
        ).total_seconds() * 1000

        return IngestionResult(
            document_id=document_id,
            title=document_title,
            chunks_created=len(chunks),
            processing_time_ms=processing_time,
            errors=[]
        )

    async def ingest_documents(
        self,
        progress_callback: Optional[callable] = None
    ) -> List[IngestionResult]:
        """
        Ingest all documents from the configured source (local or Google Drive).

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            List of ingestion results
        """
        if not self._initialized:
            await self.initialize()

        # Clean existing data if requested
        if self.clean_before_ingest:
            await self._clean_databases()

        # If source is Google Drive, download files first
        if self.source_type == "gdrive":
            self.documents_folder = self._download_from_gdrive()

        # Find all supported document files
        document_files = self._find_document_files()

        if not document_files:
            logger.warning(
                f"No supported document files found in {self.documents_folder}"
            )
            return []

        logger.info(f"Found {len(document_files)} document files to process")

        results = []

        for i, file_path in enumerate(document_files):
            try:
                logger.info(
                    f"Processing file {i+1}/{len(document_files)}: {file_path}"
                )

                result = await self._ingest_single_document(file_path)
                results.append(result)

                if progress_callback:
                    progress_callback(i + 1, len(document_files))

            except Exception as e:
                logger.exception(f"Failed to process {file_path}: {e}")
                results.append(IngestionResult(
                    document_id="",
                    title=os.path.basename(file_path),
                    chunks_created=0,
                    processing_time_ms=0,
                    errors=[str(e)]
                ))

        # Log summary
        total_chunks = sum(r.chunks_created for r in results)
        total_errors = sum(len(r.errors) for r in results)

        logger.info(
            f"Ingestion complete: {len(results)} documents, "
            f"{total_chunks} chunks, {total_errors} errors"
        )

        # Cleanup temp directory if we downloaded from Google Drive
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)
            logger.info(f"Cleaned up temp directory: {self._temp_dir}")
            self._temp_dir = None

        return results

    def _download_from_gdrive(self) -> str:
        """
        Download files from Google Drive to a temporary directory.

        Returns:
            Path to the temp directory containing downloaded files.
        """
        if not self.gdrive_folder_id:
            raise ValueError(
                "gdrive_folder_id is required when source_type='gdrive'. "
                "Set GDRIVE_FOLDER_ID env var or pass --folder-id."
            )

        try:
            from gdrive import GoogleDriveClient
        except ImportError:
            from ingestion.gdrive import GoogleDriveClient

        client = GoogleDriveClient(self.settings.gdrive_credentials_file)
        client.authenticate()

        self._temp_dir = tempfile.mkdtemp(prefix="gdrive_ingest_")
        logger.info(f"Downloading Google Drive folder {self.gdrive_folder_id} to {self._temp_dir}")

        client.download_folder(self.gdrive_folder_id, self._temp_dir)
        return self._temp_dir


