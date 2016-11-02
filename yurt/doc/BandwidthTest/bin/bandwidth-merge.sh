#!/usr/bin/env bash
HEAD="cave0";

rm ../performance/data/combined.txt

for node in 0{1..9} {10..19}; do
  NAME=$HEAD$node
  #ssh $NAME rm /tmp/$NAME-evlog.txt
  ssh $NAME cat /tmp/$NAME-evlog.txt >> ../performance/data/combined.txt
done 