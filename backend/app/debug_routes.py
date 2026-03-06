"""
Debug endpoint that provides an HTML page for testing Google OAuth
"""

from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
import os
from fastapi import Query
from . import crud, schemas
from .database import get_db

debug_router = APIRouter(prefix="/debug", tags=["Debug"])

@debug_router.get("/oauth-test", response_class=HTMLResponse)
def oauth_debug_page():
    """Interactive OAuth debugging page"""
    
    client_id = os.getenv("GOOGLE_CLIENT_ID", "NOT SET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "NOT SET")
    frontend_url = os.getenv("FRONTEND_REDIRECT_URL", "NOT SET")
    
    configured = all([
        os.getenv("GOOGLE_CLIENT_ID"),
        os.getenv("GOOGLE_CLIENT_SECRET"),
        os.getenv("GOOGLE_REDIRECT_URI")
    ])
    
    status_color = "green" if configured else "red"
    status_text = "✅ Configured" if configured else "❌ Not Configured"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Google OAuth Debugger - Zapplic</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 800px;
                width: 100%;
                padding: 40px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
                font-size: 28px;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 30px;
                font-size: 14px;
            }}
            .status {{
                display: inline-block;
                padding: 8px 16px;
                border-radius: 20px;
                background: #{status_color}33;
                color: #{status_color};
                font-weight: bold;
                margin-bottom: 20px;
                font-size: 14px;
            }}
            .section {{
                margin-bottom: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }}
            .section h2 {{
                font-size: 16px;
                color: #333;
                margin-bottom: 12px;
            }}
            .config-item {{
                margin-bottom: 12px;
                padding: 10px;
                background: white;
                border-radius: 6px;
                border-left: 3px solid #ddd;
            }}
            .config-item.ok {{
                border-left-color: #22c55e;
                background: #f0fdf4;
            }}
            .config-item.error {{
                border-left-color: #ef4444;
                background: #fef2f2;
            }}
            .config-key {{
                font-weight: bold;
                color: #667eea;
                font-size: 13px;
                margin-bottom: 4px;
            }}
            .config-value {{
                color: #666;
                font-family: monospace;
                font-size: 12px;
                word-break: break-all;
            }}
            .button-group {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .button {{
                padding: 12px 24px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: 600;
                font-size: 14px;
                border: none;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .button.primary {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .button.primary:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }}
            .button.secondary {{
                background: white;
                color: #667eea;
                border: 2px solid #667eea;
            }}
            .button.secondary:hover {{
                background: #f8f9fa;
            }}
            .issues {{
                background: #fef3c7;
                border-left-color: #f59e0b;
                color: #92400e;
            }}
            .issues h3 {{
                margin-top: 12px;
                margin-bottom: 8px;
            }}
            .issues ul {{
                margin-left: 20px;
                margin-top: 8px;
            }}
            .issues li {{
                margin-bottom: 6px;
            }}
            .step {{
                display: flex;
                gap: 12px;
                margin-bottom: 12px;
            }}
            .step-number {{
                background: #667eea;
                color: white;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
                font-weight: bold;
                font-size: 12px;
            }}
            .step-content {{
                font-size: 13px;
                line-height: 1.5;
            }}
            code {{
                background: #f3f4f6;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Google OAuth Debugger</h1>
            <p class="subtitle">Zapplic OAuth Configuration Tool</p>
            
            <div class="status">{status_text}</div>
            
            {f'''
            <div class="section">
                <h2>📋 Configuration Status</h2>
                <div class="config-item {'ok' if os.getenv('GOOGLE_CLIENT_ID') else 'error'}">
                    <div class="config-key">GOOGLE_CLIENT_ID</div>
                    <div class="config-value">{client_id[:50] + '...' if len(client_id) > 50 else client_id}</div>
                </div>
                <div class="config-item {'ok' if os.getenv('GOOGLE_CLIENT_SECRET') else 'error'}">
                    <div class="config-key">GOOGLE_CLIENT_SECRET</div>
                    <div class="config-value">{'***HIDDEN***' if os.getenv('GOOGLE_CLIENT_SECRET') else 'NOT SET'}</div>
                </div>
                <div class="config-item {'ok' if os.getenv('GOOGLE_REDIRECT_URI') else 'error'}">
                    <div class="config-key">GOOGLE_REDIRECT_URI</div>
                    <div class="config-value">{redirect_uri}</div>
                </div>
                <div class="config-item {'ok' if os.getenv('FRONTEND_REDIRECT_URL') else 'error'}">
                    <div class="config-key">FRONTEND_REDIRECT_URL</div>
                    <div class="config-value">{frontend_url}</div>
                </div>
            </div>
            ''' if configured else '''
            <div class="section issues">
                <h2>⚠️ Configuration Issues</h2>
                <p>Missing required environment variables in .env file:</p>
                <ul>
                    <li>GOOGLE_CLIENT_ID</li>
                    <li>GOOGLE_CLIENT_SECRET</li>
                    <li>GOOGLE_REDIRECT_URI</li>
                    <li>FRONTEND_REDIRECT_URL (optional)</li>
                </ul>
                <h3>How to fix:</h3>
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-content">Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Google Cloud Console</a></div>
                </div>
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-content">Create OAuth 2.0 Credentials (Web Application)</div>
                </div>
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-content">Add redirect URI: <code>http://localhost:8000/api/auth/google/callback</code></div>
                </div>
                <div class="step">
                    <div class="step-number">4</div>
                    <div class="step-content">Update your .env file with the credentials</div>
                </div>
                <div class="step">
                    <div class="step-number">5</div>
                    <div class="step-content">Restart the backend server and refresh this page</div>
                </div>
            </div>
            '''}
            
            <div class="section">
                <h2>🚀 Quick Links</h2>
                <div class="button-group">
                    {f'<a href="/api/auth/google/test-login" class="button primary">Start Login Flow</a>' if configured else ''}
                    <a href="/api/auth/google/config" class="button secondary">View JSON Config</a>
                </div>
            </div>
            
            <div class="section">
                <h2>❓ Common Errors & Solutions</h2>
                <div class="issues">
                    <h3>invalid_grant Error</h3>
                    <ul>
                        <li><strong>Already Used:</strong> Each OAuth code can only be used ONCE</li>
                        <li><strong>Expired:</strong> Codes expire after 10 minutes</li>
                        <li><strong>URI Mismatch:</strong> Redirect URI must match exactly in Google Console</li>
                    </ul>
                    <p style="margin-top: 10px;"><strong>Solution:</strong> Clear cookies, try incognito mode, or wait and try again</p>
                </div>
            </div>
            
            <div class="section">
                <h2>📖 Testing Steps</h2>
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-content">Verify all config values above are correct</div>
                </div>
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-content">Clear browser cookies and cache (or use incognito)</div>
                </div>
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-content">Click "Start Login Flow" button above</div>
                </div>
                <div class="step">
                    <div class="step-number">4</div>
                    <div class="step-content">Check backend console for detailed logs</div>
                </div>
                <div class="step">
                    <div class="step-number">5</div>
                    <div class="step-content">If error: note exact error message and retry</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@debug_router.get("/vector-recall-benchmark", response_model=schemas.RecallBenchmarkResponse, summary="Benchmark Vector Search Recall")
def benchmark_vector_recall_endpoint(
    query: str = Query(..., description="Test query to evaluate index recall"),
    k: int = Query(10, description="Number of nearest neighbors to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Developer tool to measure IVFFlat index recall accuracy against an exact k-NN flat scan.
    If the true_recall_percentage drops, consider increasing 'ivfflat.probes' during querying or recreating the index with more 'lists'.
    """
    try:
        return crud.benchmark_vector_recall(db, search_query=query, k=k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")

# Export the router
__all__ = ["debug_router"]
