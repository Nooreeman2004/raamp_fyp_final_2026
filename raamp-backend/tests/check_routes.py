import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from presentation.routers import trend_signal_router

print('Router prefix:', trend_signal_router.router.prefix)
print('\nRoutes with viral or influencer:')
for route in trend_signal_router.router.routes:
    if hasattr(route, 'path'):
        if 'viral' in route.path or 'influencer' in route.path:
            methods = route.methods if hasattr(route, 'methods') else 'N/A'
            print(f'  {route.path} - methods: {methods}')
            if hasattr(route, 'endpoint'):
                print(f'    endpoint: {route.endpoint.__name__}')
