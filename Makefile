up:
	./env/bin/python3.8 src/bot.py

prod:
	pm2 start ./pm2.json
