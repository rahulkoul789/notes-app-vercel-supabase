"""
Vercel serverless function for FastAPI backend
Uses Mangum to adapt FastAPI to AWS Lambda/Vercel format
"""
import sys
import os
import traceback

# Add the app directory to the path so we can import from it
# On GitHub, your backend code is in the 'app' folder in root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add parent directory to path (where 'app' folder is)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Also add current directory
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Set environment to production for Vercel
os.environ.setdefault("ENVIRONMENT", "production")

# Try to import and create handler
# Print debug info to stderr (visible in Vercel logs)
import sys as sys_module
def debug_print(*args, **kwargs):
    print(*args, **kwargs, file=sys_module.stderr)
    sys_module.stderr.flush()

debug_print("=== Starting Vercel function initialization ===")
debug_print(f"Current dir: {current_dir}")
debug_print(f"Parent dir: {parent_dir}")
debug_print(f"Python path: {sys.path}")

try:
    debug_print("Attempting to import mangum...")
    from mangum import Mangum
    debug_print("✓ Mangum imported successfully")
    
    debug_print("Attempting to import app.main...")
    from app.main import app
    debug_print("✓ app.main imported successfully")
    
    debug_print("Creating Mangum handler...")
    handler = Mangum(app, lifespan="off")
    debug_print("✓ Handler created successfully")
    debug_print("=== Initialization complete ===")
    
except ImportError as e:
    # Handle import errors with detailed message
    error_msg = f"Import error: {str(e)}\n\n"
    error_msg += f"Python path: {sys.path}\n"
    error_msg += f"Current dir: {current_dir}\n"
    error_msg += f"Parent dir: {parent_dir}\n"
    error_msg += f"Files in parent: {os.listdir(parent_dir) if os.path.exists(parent_dir) else 'NOT FOUND'}\n"
    error_msg += f"Traceback: {traceback.format_exc()}"
    
    debug_print(f"❌ Import error: {error_msg}")
    
    def handler(event, context):
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": error_msg
        }
    
except Exception as e:
    # Handle other errors (including config errors)
    error_msg = f"Error initializing app: {str(e)}\n\n"
    error_msg += f"Error type: {type(e).__name__}\n"
    error_msg += f"Traceback: {traceback.format_exc()}\n\n"
    error_msg += "Make sure:\n"
    error_msg += "1. All environment variables are set in Vercel (SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY)\n"
    error_msg += "2. The 'app' folder exists in the root directory\n"
    error_msg += "3. All dependencies are in api/requirements.txt\n"
    error_msg += "4. You've redeployed after adding environment variables"
    
    debug_print(f"❌ Initialization error: {error_msg}")
    
    # Create a handler that returns the error in the response
    # This way you can see the error by visiting /api/health or any endpoint
    def handler(event, context):
        import json
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Initialization failed",
                "message": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "help": "Check Vercel logs for full details. Common issues: missing env vars, wrong file structure, or missing dependencies."
            }, indent=2)
        }
