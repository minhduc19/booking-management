- Restructure and reimplement like [this repo](https://youtu.be/TO4aQ3ghFOc?si=evldQVp1EQQPp0eW)
- Create a staging branch and staging environment [Done]
- Create endpoint to show bookings since 10 days ago
- Create table for listing details rather than the current hard coded mapping
- Endpoint to edit cleaning session
- Endpoint to edit cleaner
- Github action to a [server](https://github.com/andfadeev/digital-ocean-github-actions-ci)
# FastapiTemplate
# Change in test
For action to works, environment secrets need to be set up:

      DATABASE_HOSTNAME: ${{secrets.DATABASE_HOSTNAME}}
      DATABASE_PORT: ${{secrets.DATABASE_PORT}}
      DATABASE_PASSWORD: ${{secrets.DATABASE_PASSWORD}}
      DATABASE_NAME: ${{secrets.DATABASE_NAME}}
      DATABASE_USERNAME: ${{secrets.DATABASE_USERNAME}}

Go to Setting >> Secrets and variables >> Actions. This is just for a local postgres in the VM of postgress

      DATABASE_HOSTNAME="localhost"
      DATABASE_PORT="5432"
      DATABASE_PASSWORD="dory"
      DATABASE_NAME="Test"
      DATABASE_USERNAME="postgres"

For this app to be deployed on Heroku, add this step to the yml file. I also needs to set up environment variable on Heroku by going to Setting >> Config Vars. Then add the actual production environment secrets.

```
  deploy:
    runs-on: ubuntu-latest
    needs: [build]
    environment:
      name: testing
    steps: 
      - name: Deploy to server
        run: echo "deploy to server"
      - name: pulling git repo
        uses: actions/checkout@v2
      - name: deploying to Heroku
        uses: akhileshns/heroku-deploy@v3.12.14
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: ${{secrets.HEROKU_APP_NAME}}
          heroku_email: ${{secrets.HEROKU_EMAIL}}
```yml
