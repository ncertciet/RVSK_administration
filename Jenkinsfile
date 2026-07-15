pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(
            numToKeepStr: '20',
            artifactNumToKeepStr: '5'
        ))
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        APP_NAME       = 'rvsk_administration'
        IMAGE_NAME     = 'rvsk-administration'

        DEPLOY_USER    = 'ubuntu'
        DEPLOY_HOST    = '10.249.96.115'
        DEPLOY_DIR     = '/home/ubuntu/RVSK_administration'

        HOST_PORT      = '8002'
        CONTAINER_PORT = '8000'

        HEALTH_URL     = 'http://127.0.0.1:8002/health'

        KEEP_IMAGES    = '5'
    }

    stages {

        stage('Checkout Main Branch') {
            steps {
                checkout([
                    $class: 'GitSCM',

                    branches: [[
                        name: '*/main'
                    ]],

                    userRemoteConfigs: [[
                        url: 'https://github.com/ncertciet/RVSK_administration.git'
                    ]]
                ])

                script {
                    env.COMMIT_ID = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()

                    env.FULL_COMMIT_ID = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    echo "Production deployment commit: ${env.COMMIT_ID}"
                }
            }
        }

        stage('Verify SSH Connection') {
            steps {
                sh """
                    ssh \
                      -o BatchMode=yes \
                      -o ConnectTimeout=10 \
                      ${DEPLOY_USER}@${DEPLOY_HOST} \
                      'hostname && whoami'
                """
            }
        }

        stage('Verify Production Environment') {
            steps {
                sh """
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        echo "Checking Docker..."
                        docker --version

                        echo "Checking application directory..."
                        test -d ${DEPLOY_DIR}

                        echo "Checking production .env..."
                        test -f ${DEPLOY_DIR}/.env

                        echo "Checking Dockerfile..."
                        test -f ${DEPLOY_DIR}/Dockerfile

                        echo "Production environment verification successful."
                    '
                """
            }
        }

        stage('Update Production Source') {
            steps {
                sh """
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        cd ${DEPLOY_DIR}

                        echo "Fetching latest Git repository information..."
                        git fetch origin main

                        echo "Deploying exact Jenkins commit:"
                        echo "${FULL_COMMIT_ID}"

                        git checkout main
                        git reset --hard ${FULL_COMMIT_ID}

                        echo "Current deployed source commit:"
                        git rev-parse --short HEAD

                        echo "Verifying production .env still exists..."
                        test -f .env
                    '
                """
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        cd ${DEPLOY_DIR}

                        echo "Building Docker image:"
                        echo "${IMAGE_NAME}:${COMMIT_ID}"

                        docker build \
                          -t ${IMAGE_NAME}:${COMMIT_ID} \
                          .

                        docker tag \
                          ${IMAGE_NAME}:${COMMIT_ID} \
                          ${IMAGE_NAME}:latest
                    '
                """
            }
        }

        stage('Deploy with Automatic Rollback') {
            steps {
                sh """
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        cd ${DEPLOY_DIR}

                        NEW_IMAGE="${IMAGE_NAME}:${COMMIT_ID}"
                        APP_NAME="${APP_NAME}"
                        BACKUP_NAME="${APP_NAME}_rollback"

                        echo "======================================"
                        echo "Starting Production deployment"
                        echo "New image: \$NEW_IMAGE"
                        echo "======================================"

                        OLD_IMAGE=""

                        if docker inspect "\$APP_NAME" >/dev/null 2>&1; then

                            OLD_IMAGE=\$(docker inspect \
                              --format="{{.Config.Image}}" \
                              "\$APP_NAME")

                            echo "Current image: \$OLD_IMAGE"

                            docker rm -f "\$BACKUP_NAME" \
                              >/dev/null 2>&1 || true

                            docker rename \
                              "\$APP_NAME" \
                              "\$BACKUP_NAME"

                            docker stop \
                              "\$BACKUP_NAME"
                        else
                            echo "No existing container found."
                        fi

                        echo "Starting new Production container..."

                        docker run -d \
                          --name "\$APP_NAME" \
                          --restart unless-stopped \
                          --env-file ${DEPLOY_DIR}/.env \
                          -p 127.0.0.1:${HOST_PORT}:${CONTAINER_PORT} \
                          "\$NEW_IMAGE"

                        echo "Waiting for application startup..."

                        HEALTHY=false

                        for i in \$(seq 1 12); do

                            echo "Health check attempt \$i/12"

                            if curl \
                              --silent \
                              --show-error \
                              --fail \
                              ${HEALTH_URL} \
                              >/dev/null; then

                                HEALTHY=true
                                break
                            fi

                            sleep 5
                        done

                        if [ "\$HEALTHY" = "true" ]; then

                            echo "======================================"
                            echo "Deployment successful"
                            echo "======================================"

                            docker rm -f "\$BACKUP_NAME" \
                              >/dev/null 2>&1 || true

                            exit 0
                        fi

                        echo "======================================"
                        echo "NEW DEPLOYMENT FAILED"
                        echo "Starting automatic rollback"
                        echo "======================================"

                        echo "Failed container logs:"
                        docker logs \
                          --tail 100 \
                          "\$APP_NAME" || true

                        docker rm -f \
                          "\$APP_NAME" || true

                        if docker inspect \
                          "\$BACKUP_NAME" \
                          >/dev/null 2>&1; then

                            docker rename \
                              "\$BACKUP_NAME" \
                              "\$APP_NAME"

                            docker start \
                              "\$APP_NAME"

                            echo "Waiting for rollback container..."

                            sleep 5

                            if curl \
                              --silent \
                              --show-error \
                              --fail \
                              ${HEALTH_URL} \
                              >/dev/null; then

                                echo "Rollback successful."
                            else
                                echo "CRITICAL: Rollback container is unhealthy."
                            fi

                        else
                            echo "CRITICAL: No rollback container available."
                        fi

                        exit 1
                    '
                """
            }
        }

        stage('Verify Deployment') {
            steps {
                sh """
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        echo "===== CONTAINER ====="
                        docker ps \
                          --filter name=${APP_NAME}

                        echo "===== RUNNING IMAGE ====="
                        docker inspect \
                          ${APP_NAME} \
                          --format="{{.Config.Image}}"

                        echo "===== HEALTH ====="
                        curl --fail \
                          ${HEALTH_URL}

                        echo
                        echo "===== NGINX ADMINISTRATION ENDPOINT ====="
                        curl --fail \
                          http://127.0.0.1/administration/openapi.json \
                          >/dev/null

                        echo "Production deployment verified."
                    '
                """
            }
        }

        stage('Docker Image Cleanup') {
            steps {
                sh """
                    ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                        set -e

                        echo "Docker disk usage before cleanup:"
                        docker system df

                        CURRENT_IMAGE=\$(docker inspect \
                          --format="{{.Config.Image}}" \
                          ${APP_NAME})

                        echo "Current running image:"
                        echo "\$CURRENT_IMAGE"

                        echo "Removing dangling images..."
                        docker image prune -f

                        echo "Keeping the newest ${KEEP_IMAGES} tagged application images..."

                        docker images \
                          ${IMAGE_NAME} \
                          --format "{{.Repository}}:{{.Tag}} {{.CreatedAt}}" \
                          | grep -v ":latest " \
                          | sort -rk2,3 \
                          | awk "NR>${KEEP_IMAGES} {print \\\$1}" \
                          | while read IMAGE; do

                                if [ "\$IMAGE" != "\$CURRENT_IMAGE" ]; then
                                    echo "Removing old image: \$IMAGE"
                                    docker image rm "\$IMAGE" || true
                                fi

                            done

                        echo "Docker disk usage after cleanup:"
                        docker system df
                    '
                """
            }
        }
    }

    post {

        success {
            echo """
========================================
PRODUCTION DEPLOYMENT SUCCESSFUL
Application : ${APP_NAME}
Host        : ${DEPLOY_HOST}
Commit      : ${COMMIT_ID}
Port        : ${HOST_PORT}
========================================
"""
        }

        failure {
            echo """
========================================
PRODUCTION DEPLOYMENT FAILED
Check the Jenkins deployment logs.
Automatic rollback was attempted.
========================================
"""
        }

        always {
            cleanWs()
        }
    }
}
