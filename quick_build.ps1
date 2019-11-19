Clear-Host

# Copy existing database
# pg_dump -C -h <source ip> -U <source username> <source database> | psql -h localhost -U <destination username> <destination database>

# Making Migrations for Django
# Write to the host since the command usually spits out "no changes detected" and could be confusing
Write-Host "Making Migrations for Django before building..."
docker run --rm --mount type=bind,src=E:/Projects/Discord/Live-Bot,dst=/code --env-file dev.env bsquidwrd/livebot python manage.py makemigrations

# Build image
docker build --rm -f "Dockerfile" -t bsquidwrd/livebot .

# Spinning up replacement containers and removing any orphans
docker-compose up --build -d --remove-orphans

# Showing logs for the running containers
docker-compose logs -f
