echo "-------------------UPDATE REPO-------------------"
git pull
echo "--------------------BUILD IMAGE------------------"
docker compose build
echo "------------------RESTART CONTAINER--------------"
docker compose up -d
