from app import create_minimal_app

min_app = None

def _make_min_app():
	global min_app
	if min_app is None:
		min_app = create_minimal_app()
	return min_app
