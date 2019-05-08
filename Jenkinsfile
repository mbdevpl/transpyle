pipeline {
  agent none
  environment {
    CODECOV_TOKEN = credentials('codecov-token-transpyle')
  }
  stages { stage('Test') { parallel {
    stage('C') {
      agent { label 'x86_64 && gpu && pgi' }
      steps {
        sh "TEST_LONG=1 python3 -m coverage run --branch --source . -m unittest -v test.test_c"
        sh "if [[ \"${env.BRANCH_NAME}\" == \"master\" ]] ; then codecov --build \"${NODE_NAME} ${BUILD_DISPLAY_NAME}\" --token \"${CODECOV_TOKEN}\" ; fi"
      }
    }
    stage('C++') {
      agent { label 'x86_64 && gpu && pgi' }
      steps {
        sh "TEST_LONG=1 python3 -m coverage run --branch --source . -m unittest -v test.test_cpp"
        sh "if [[ \"${env.BRANCH_NAME}\" == \"master\" ]] ; then codecov --build \"${NODE_NAME} ${BUILD_DISPLAY_NAME}\" --token \"${CODECOV_TOKEN}\" ; fi"
      }
    }
    stage('Fortran') {
      agent { label 'x86_64 && gpu && pgi' }
      steps {
        sh "TEST_LONG=1 python3 -m coverage run --branch --source . -m unittest -v test.test_fortran"
        sh "if [[ \"${env.BRANCH_NAME}\" == \"master\" ]] ; then codecov --build \"${NODE_NAME} ${BUILD_DISPLAY_NAME}\" --token \"${CODECOV_TOKEN}\" ; fi"
      }
    }
    stage('Python') {
      agent { label 'x86_64 && gpu && pgi' }
      steps {
        sh "TEST_LONG=1 python3 -m coverage run --branch --source . -m unittest -v test.test_python"
        sh "if [[ \"${env.BRANCH_NAME}\" == \"master\" ]] ; then codecov --build \"${NODE_NAME} ${BUILD_DISPLAY_NAME}\" --token \"${CODECOV_TOKEN}\" ; fi"
      }
    }
    stage('Python as IR') {
      agent { label 'x86_64 && gpu && pgi' }
      steps {
        sh "TEST_LONG=1 python3 -m coverage run --branch --source . -m unittest -v test.test_pair"
        sh "if [[ \"${env.BRANCH_NAME}\" == \"master\" ]] ; then codecov --build \"${NODE_NAME} ${BUILD_DISPLAY_NAME}\" --token \"${CODECOV_TOKEN}\" ; fi"
      }
    }
    stage('Integration') {
      agent { label 'x86_64 && gpu && pgi' }
      steps {
        sh "TEST_LONG=1 python3 -m coverage run --branch --source . -m unittest -v test.test_integration"
        sh "if [[ \"${env.BRANCH_NAME}\" == \"master\" ]] ; then codecov --build \"${NODE_NAME} ${BUILD_DISPLAY_NAME}\" --token \"${CODECOV_TOKEN}\" ; fi"
      }
    }
    stage('Apps') {
      agent { label 'x86_64 && gpu && pgi' }
      steps {
        sh "TEST_APPS_ROOT=~/Projects/ TEST_LONG=1 python3 -m coverage run --branch --source . -m unittest -v test.test_apps"
        sh "if [[ \"${env.BRANCH_NAME}\" == \"master\" ]] ; then codecov --build \"${NODE_NAME} ${BUILD_DISPLAY_NAME}\" --token \"${CODECOV_TOKEN}\" ; fi"
      }
    }
    stage('Performance') {
      agent { label 'x86_64 && gpu && pgi' }
      steps {
        sh "TEST_LONG=1 python3 -m coverage run --branch --source . -m unittest -v test.test_performance"
        sh "if [[ \"${env.BRANCH_NAME}\" == \"master\" ]] ; then codecov --build \"${NODE_NAME} ${BUILD_DISPLAY_NAME}\" --token \"${CODECOV_TOKEN}\" ; fi"
      }
    }
  } } }
}
