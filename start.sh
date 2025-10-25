#TODO: check to use update or not

eval $(pixi shell-hook)
python update.py && python -m bot


#OLD from debian deploy
#sudo kill $(pgrep -f "/var/www/ml/venv/bin/python3 /var/www/ml/venv/bin/gunicorn")
#source ./venv/bin/activate
#python3 -m bot
#!/bin/bash
#source /www/ml/venv/bin/activate
#nohup python3 -m bot &
