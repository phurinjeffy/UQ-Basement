import json
import asyncio
import httpx
from pathlib import Path
from typing import Dict, Any
import os
from datetime import datetime

class QuestionImporter:
    def __init__(self, api_base_url: str = "http://localhost:8000/api/v1"):
        self.api_base_url = api_base_url
        self.bulk_import_endpoint = f"{api_base_url}/questions/bulk-import"
    
    async def import_from_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read JSON file and import questions to database
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dict containing import results
        """
        try:
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            
            print(f"📁 Reading JSON file: {file_path}")
            print(f"📊 Found {len(json_data.get('questions', []))} questions and {len(json_data.get('mock_exam', []))} mock exam questions")
            
            # Send to bulk import endpoint
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.bulk_import_endpoint,
                    json=json_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 201:
                    result = response.json()
                    print(f"✅ Successfully imported {result['imported_count']} questions!")
                    
                    if result.get('skipped_count', 0) > 0:
                        print(f"⚠️  Skipped {result['skipped_count']} questions (empty or invalid)")
                    
                    if result.get('errors'):
                        print(f"❌ Errors encountered: {len(result['errors'])}")
                        for error in result['errors'][:3]:  # Show first 3 errors
                            print(f"   - {error}")
                    
                    return result
                else:
                    error_msg = f"Failed to import: {response.status_code} - {response.text}"
                    print(f"❌ {error_msg}")
                    return {"success": False, "error": error_msg}
                    
        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def import_from_json_file_sync(self, file_path: str) -> Dict[str, Any]:
        """
        Synchronous version of import_from_json_file
        """
        return asyncio.run(self.import_from_json_file(file_path))
    
    async def watch_and_import(self, file_path: str, check_interval: int = 5):
        """
        Watch for file changes and automatically import when updated
        
        Args:
            file_path: Path to the JSON file to watch
            check_interval: How often to check for changes (seconds)
        """
        file_path = Path(file_path)
        last_modified = None
        
        print(f"👀 Watching file: {file_path}")
        print(f"🔄 Check interval: {check_interval} seconds")
        print("Press Ctrl+C to stop watching...")
        
        try:
            while True:
                if file_path.exists():
                    current_modified = file_path.stat().st_mtime
                    
                    if last_modified is None:
                        last_modified = current_modified
                        print(f"📄 Initial file detected: {datetime.fromtimestamp(current_modified)}")
                    elif current_modified > last_modified:
                        print(f"🔄 File updated: {datetime.fromtimestamp(current_modified)}")
                        result = await self.import_from_json_file(str(file_path))
                        
                        if result.get('success', True):  # Assume success if key not present
                            print(f"✅ Auto-import completed at {datetime.now().strftime('%H:%M:%S')}")
                        else:
                            print(f"❌ Auto-import failed: {result.get('error', 'Unknown error')}")
                        
                        last_modified = current_modified
                else:
                    if last_modified is not None:
                        print(f"⚠️  File no longer exists: {file_path}")
                        last_modified = None
                
                await asyncio.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n👋 Stopping file watcher...")

# Utility functions for easy usage
async def import_questions_from_file(file_path: str, api_url: str = "http://localhost:8000/api/v1"):
    """
    Quick function to import questions from a JSON file
    
    Args:
        file_path: Path to your JSON file
        api_url: Base URL of your FastAPI server
        
    Returns:
        Import results
    """
    importer = QuestionImporter(api_url)
    return await importer.import_from_json_file(file_path)

def import_questions_from_file_sync(file_path: str, api_url: str = "http://localhost:8000/api/v1"):
    """
    Synchronous version - easier to use in scripts
    """
    return asyncio.run(import_questions_from_file(file_path, api_url))

async def watch_json_file(file_path: str, api_url: str = "http://localhost:8000/api/v1", interval: int = 5):
    """
    Watch a JSON file and auto-import when it changes
    """
    importer = QuestionImporter(api_url)
    await importer.watch_and_import(file_path, interval)

# Example usage and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python importer.py <json_file_path> [api_url]")
        print("  python importer.py watch <json_file_path> [api_url] [interval_seconds]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "watch" and len(sys.argv) >= 3:
        # Watch mode
        file_path = sys.argv[2]
        api_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8000/api/v1"
        interval = int(sys.argv[4]) if len(sys.argv) > 4 else 5
        
        print("🚀 Starting file watcher mode...")
        asyncio.run(watch_json_file(file_path, api_url, interval))
        
    else:
        # Single import mode
        file_path = sys.argv[1]
        api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000/api/v1"
        
        print("🚀 Starting single import...")
        result = import_questions_from_file_sync(file_path, api_url)
        
        if result.get('success', True):
            print(f"🎉 Import completed successfully!")
            print(f"📊 Imported: {result.get('imported_count', 0)} questions")
        else:
            print(f"💥 Import failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)