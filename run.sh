rm ./server/logs/*
echo '===== logs deleted ====='

cd ./AIC22-Client-Python/
rm -rf src/dist/ src/build/
pyinstaller --onefile src/client.py
echo '===== opponent 1 ready ====='

# cd ../AIC22-Client-Python2/
# rm -rf src/dist/ src/build/
# pyinstaller --onefile src/client.py
echo '===== opponent 2 ready ====='

cd ../server
# java -jar hideandseek-0.1.1.jar --first-team=../AIC22-Client-Python/dist/client --second-team=../AIC22-Client-Python/dist/client resources/game.yml resources/map.json

# Play with random oponent
java -jar hideandseek-0.1.1.jar --first-team=../AIC22-Client-Python/dist/client --second-team=../AIC22-Client-Python2/dist/client resources/game.yml resources/map.json


