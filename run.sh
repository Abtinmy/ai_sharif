rm ./server/logs/*
rm ./server/log.log
echo '===== logs deleted ====='

cd ./AIC22-Client-Python/
rm -rf src/dist/ src/build/
echo '===== folder dist and build deteled ====='

pyinstaller --onefile src/client.py
echo '===== pyinstaller client done ====='
cd ../server
java -jar hideandseek-0.0.7.jar --first-team=../AIC22-Client-Python/dist/client --second-team=../AIC22-Client-Python/dist/client resources/game.yml resources/map.json

