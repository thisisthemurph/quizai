dev:
	uvicorn api:app --reload

i:
	pip install -r requirements.txt

tw:
	./tailwindcss -i ./styles/tailwind.css -o ./static/css/app.css --watch

tw-ref:
	rm --force ./static/css/app.css
	make tw