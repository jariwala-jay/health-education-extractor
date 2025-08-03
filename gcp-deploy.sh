#!/bin/bash

# Google Cloud Platform Deployment Script for Health Education Extractor
# This script automates the deployment process to GCP App Engine

set -e  # Exit on any error

echo "🚀 Starting GCP Deployment Process..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed."
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with gcloud."
    echo "Please run: gcloud auth login"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No GCP project set."
    echo "Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Deploying to project: $PROJECT_ID"

# Prompt for environment variables
echo ""
echo "🔐 Setting up secrets in Google Secret Manager..."
echo "We need to create secrets for sensitive environment variables."

# Function to create or update secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if gcloud secrets describe $secret_name --project=$PROJECT_ID &>/dev/null; then
        echo "Updating existing secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=-
    else
        echo "Creating new secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=-
    fi
}

# Read secrets from .env file if it exists
if [ -f "backend/.env" ]; then
    echo "📖 Reading secrets from backend/.env file..."
    
    # Extract values from .env file
    MONGODB_URL=$(grep "^MONGODB_URL=" backend/.env | cut -d '=' -f2- | sed 's/^"//' | sed 's/"$//')
    SECRET_KEY=$(grep "^SECRET_KEY=" backend/.env | cut -d '=' -f2- | sed 's/^"//' | sed 's/"$//')
    ADMIN_PASSWORD=$(grep "^ADMIN_PASSWORD=" backend/.env | cut -d '=' -f2- | sed 's/^"//' | sed 's/"$//')
    GEMINI_API_KEY=$(grep "^GEMINI_API_KEY=" backend/.env | cut -d '=' -f2- | sed 's/^"//' | sed 's/"$//')
    UNSPLASH_ACCESS_KEY=$(grep "^UNSPLASH_ACCESS_KEY=" backend/.env | cut -d '=' -f2- | sed 's/^"//' | sed 's/"$//')
    UNSPLASH_SECRET_KEY=$(grep "^UNSPLASH_SECRET_KEY=" backend/.env | cut -d '=' -f2- | sed 's/^"//' | sed 's/"$//')
    
    # Create secrets
    [ ! -z "$MONGODB_URL" ] && create_or_update_secret "mongodb-url" "$MONGODB_URL"
    [ ! -z "$SECRET_KEY" ] && create_or_update_secret "jwt-secret-key" "$SECRET_KEY"
    [ ! -z "$ADMIN_PASSWORD" ] && create_or_update_secret "admin-password" "$ADMIN_PASSWORD"
    [ ! -z "$GEMINI_API_KEY" ] && create_or_update_secret "gemini-api-key" "$GEMINI_API_KEY"
    [ ! -z "$UNSPLASH_ACCESS_KEY" ] && create_or_update_secret "unsplash-access-key" "$UNSPLASH_ACCESS_KEY"
    [ ! -z "$UNSPLASH_SECRET_KEY" ] && create_or_update_secret "unsplash-secret-key" "$UNSPLASH_SECRET_KEY"
else
    echo "⚠️  No .env file found. You'll need to create secrets manually."
    echo "Please create the following secrets in Google Secret Manager:"
    echo "- mongodb-url"
    echo "- jwt-secret-key"
    echo "- admin-password"
    echo "- gemini-api-key"
    echo "- unsplash-access-key"
    echo "- unsplash-secret-key"
fi

# Enable required APIs
echo ""
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable appengine.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Deploy to App Engine
echo ""
echo "🚀 Deploying to Google App Engine..."
cd backend
gcloud app deploy app.yaml --quiet

# Get the deployed URL
echo ""
echo "✅ Deployment completed!"
APP_URL=$(gcloud app describe --format="value(defaultHostname)")
echo "🌐 Your app is available at: https://$APP_URL"

echo ""
echo "📋 Next steps:"
echo "1. Update your frontend's API URL to: https://$APP_URL"
echo "2. Test the deployment: https://$APP_URL/health"
echo "3. Deploy your frontend to Vercel"

echo ""
echo "🔐 Security reminders:"
echo "- All secrets are stored in Google Secret Manager"
echo "- The app is served over HTTPS"
echo "- Consider setting up custom domain and SSL" 