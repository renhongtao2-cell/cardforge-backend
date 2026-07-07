from app.config import APP_NAME, APP_VERSION

app = None

def get_app():
    global app
    if app is None:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from routes.cards import router as cards_router
        from routes.api import router as api_router
        
        app = FastAPI(
            title=APP_NAME,
            version=APP_VERSION,
            description='AI-powered URL preview card generator',
        )
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )
        
        app.include_router(cards_router, prefix='/api/cards', tags=['cards'])
        app.include_router(api_router, prefix='/api', tags=['api'])
        
        @app.get('/')
        def root():
            return {
                'name': APP_NAME,
                'version': APP_VERSION,
                'status': 'running',
                'docs': '/docs',
            }
        
        @app.get('/health')
        def health():
            return {'status': 'ok'}
    
    return app
