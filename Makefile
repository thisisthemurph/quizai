dev:
	uvicorn api:app --reload

i:
	pip install -r requirements.txt

tw:
	.\tailwindcss.exe -i .\styles\tailwind.css -o .\static\css\app.css --watch

tw-ref:
	del .\static\css\app.css
	make tw