echo "--------------------BUILD IMAGE------------------"
docker compose build
echo "--------------------START CONTAINER--------------"
docker compose up -d
