pipeline {
  agent none
  environment {
    CODECOV_TOKEN = credentials('codecov-token-transpyle')
  }
  stages { stage('Test') { parallel {
    stage('Test Fortran apps') {
      agent any
      steps {
        sh "TEST_APPS_ROOT=~/Projects/ TEST_FLASH=1 python3.6 -m coverage run --branch --source . -m unittest -v test.fortran.test_apps"
        sh "if [[ \"${env.BRANCH_NAME}\" == \"master\" ]] ; then codecov --build \"${NODE_NAME} ${BUILD_DISPLAY_NAME}\" --token \"${CODECOV_TOKEN}\" ; fi"
      }
    }
    stage('Test performance') {
      agent any
      steps {
        sh '''
          source /etc/profile.d/modules.sh &&
          source ~/Software/Environment/bash/spack.bashrc &&
          spack load llvm@7.0.1%gcc@4.8.5 &&
          spack load gcc@8.3.0%gcc@4.8.5 +piclibs +nvptx &&
          spack load libffi@3.2.1%gcc@8.3.0 &&
          module list &&
          TEST_LONG=1 python3.6 -m coverage run --branch --source . -m unittest -v test.test_performance
          '''
        sh "if [[ \"${env.BRANCH_NAME}\" == \"master\" ]] ; then codecov --build \"${NODE_NAME} ${BUILD_DISPLAY_NAME}\" --token \"${CODECOV_TOKEN}\" ; fi"
      }
    }
  } } }
}
