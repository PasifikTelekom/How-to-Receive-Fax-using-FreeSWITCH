# Réception des arguments
REMOTE_STATION=$1
LOCAL_STATION=$2
PAGES=$3
TOTAL_PAGES=$4
CODE=$5
CALLER=$6
UUID=$7

# On passe les variables à un script python qui fera le reste du travail
/usr/bin/python /usr/local/freeswitch/scripts/process-rxfax-mysql.py "$REMOTE_STATION" "$LOCAL_STATION" "$PAGES" "$TOTAL_PAGES" "$CODE" "$CALLER" "$UUID"