start:
	echo 'Starting Simulation Server'
	uvicorn main:app --host 0.0.0.0 --port 8000  --reload