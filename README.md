# proj
## UPD: guincorn корректно работает с бд
run virtualenv

install dependencies from requirments.txt

gunicorn -b adress:port -w 4 --threads 4 -t 360 --access-logfile ~/ftt_log.txt fin:app

http://donkey1.nosoc.io:5050/

## Known issues:
Даты-время надо передавать в график таймстампом, иначе некорректно отображается их порядок на графике
