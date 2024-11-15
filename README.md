# aiLEADS

aiLEADS was a lightweight, AI-powered B2B lead generation platform that helps businesses find potential customers quickly and efficiently. People didn't find it quicker or more efficient than doing a Google search, so they didn't use it. Now I'm posting it here.

## Features (Marketing Version)

- **AI-Powered Search**: Intelligent query processing and lead validation
- **Fresh Data**: Real-time lead generation from current internet sources
- **Easy Onboarding**: Quick setup with minimal learning curve
- **Usage-Based Pricing**: Pay-as-you-go model with credits system
- **Contact Discovery**: Automated contact information extraction
- **Lead Sources**: Identifies both direct leads and valuable lead source pages
- **Export Capabilities**: Export leads to CSV for follow-up

## Features (Technical Version)

- **Search**: Uses GPT-4 or GPT-4-mini to read search results and select relevant leads and lead sources
- **Contact Discovery**: Uses GPT-4 or GPT-4-mini to extract contact information from leads
- **Contact Validation**: Uses GPT-4 or GPT-4-mini to find contact information on leads
- **Lead Validation**: Uses GPT-4 or GPT-4-mini to validate leads
- **Personalized Lead Model**: Trains and uses custom FastText model to quickly score lead relevance to a user

## Technology Stack

- Backend: Flask (Python)
- Database: SQLAlchemy, PostgreSQL
- Real-time Communication: Socket.IO
- Caching: Redis
- Task Queue: RQ (Redis Queue)
- Frontend: Bootstrap, JavaScript, HTML, CSS
- Email: Flask-Mail, Sendgrid
- Authentication: Flask-Login
- AI/ML: OpenAI GPT, FastText

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3+
- Redis Server
- PostgreSQL

## Getting Started

1. Clone the repository
2. Create a virtual environment:
	```bash
	python -m venv venv
	source venv/bin/activate  # On Windows: venv\Scripts\activate
	```
3. Install dependencies:
	```bash
	pip install -r requirements.txt
	```
4. Set up environment variables in .env:
	```
	FLASK_ENV="dev"
	FLASK_APP="app.py"
	SECRET_KEY='your_secret_key'
	PROJECT_ID='your_project_id'
	GOOGLE_APPLICATION_CREDENTIALS='/path/to/google_creds.json'
	DB_NAME="your_db_name"
	DB_USER="your_db_user"
	DB_PASS="your_db_password"
	DB_HOST="localhost"
	DEV_SQLALCHEMY_DATABASE_URI="your_dev_db_uri"
	PROD_SQLALCHEMY_DATABASE_URI="your_prod_db_uri"
	```

5. Initialize database:
	```bash
	flask db init
	flask db migrate
	flask db upgrade
	```

## Usage

1. Start Redis server
	```bash
	redis-server
	```
2. Start Redis Worker:
	```bash
	rq worker --worker-class rq.SimpleWorker high_priority low_priority
	```
3. Run Flask application:
	```bash
	python run.py
	```


## Project Structure

- `/app`: Main application directory
  - `/llm`: AI/ML related code including prompt templates and model interactions
  - `/models`: Database models
  - `/static`: Static files (CSS, JavaScript, images)
  - `/templates`: HTML templates
  - `/utils`: Utility functions

## How It Works (User Version)

1. Submit a search query
2. AI processes and optimizes your search
3. System identifies both leads and lead sources
4. Automated contact discovery
5. Quality validation and scoring
6. Export and follow up

## How It Works (Technical Version)

1. Submit a search query
   - AI may suggest a better query based on user settings and past successful queries
2. Sends query to SerpAPI for search results
3. Parse search results with LLM to determine relevance
4. Add relevant results as sources or leads
5. Check all sources for additional sources and leads
6. Check all leads for contact information and relevance
7. Score leads relevance to user (not currently implemented but was implemented in a previous version)
8. Store leads in DB and send to front-end via socket


Steps 2-8 are handled by redis worker.


## Credit System

The platform uses a credit-based system where:
- Most actions cost around 10-100 credits
- Costs vary based on tokens consumed during the request
- Users can switch to GPT-4o for better quality at a higher cost
- Default is GPT-4o-mini
- New users get 5,000 free credits for email verification
- First 20,000 credits are offered at 50% off

## Contributing

While this project is no longer actively maintained, feel free to fork and modify it for your own use. If you make improvements, consider submitting a pull request.

## License

This project is open source and available under the MIT License.