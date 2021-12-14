#!/bin/sh

#catch the TEM signal and then exit
trap "exit" TERM SIGINT SIGTERM

while true;
do
  echo "Keeping busy.."
  sleep 5;
done
