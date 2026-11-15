#!/usr/bin/env bash
# Instaluje (albo aktualizuje) zbieracz Trendo obok istniejących aplikacji.
# Dodaje tylko: /opt/trendo, /var/lib/trendo, /etc/trendo.env, usługę trendo i własną trasę w /etc/caddy/conf.d.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_SUSPEND=1
main() {
[ "$(id -u)" -eq 0 ] || { echo "Uruchom jako root."; exit 1; }
command -v caddy >/dev/null || { echo "STOP: ten skrypt wymaga działającego Caddy."; exit 2; }
PY=/root/trendo-scraper/bin/python
[ -x "$PY" ] || { echo "STOP: brak ~/trendo-scraper (najpierw instalacja przeglądarki)."; exit 2; }
IP=$(curl -4fsS https://api.ipify.org)
HOST="${IP//./-}.sslip.io"
PORT=18890
if ss -ltnpH "( sport = :$PORT )" | grep -v python | grep -q .; then echo "STOP: port $PORT jest zajęty przez inną aplikację."; exit 2; fi
DIR=/opt/trendo
echo "Pobieram najnowszą wersję z GitHuba..."
mkdir -p "$DIR" /var/lib/trendo
TMP=$(mktemp -d)
curl -fsSL https://codeload.github.com/lewym90/trendo/tar.gz/main | tar -xz -C "$TMP"
rm -rf "$DIR/trendo"
cp -r "$TMP"/trendo-main/serwer/. "$DIR"/
rm -rf "$TMP"
[ -f /etc/trendo.env ] || ( umask 077; printf 'PORT=%s\nTRENDO_DANE=/var/lib/trendo\nSERPAPI_LIMIT_DZIENNY=8\n' "$PORT" > /etc/trendo.env )
cat > /etc/systemd/system/trendo.service <<EOF
[Unit]
Description=Trendo zbieracz
After=network-online.target
[Service]
EnvironmentFile=/etc/trendo.env
WorkingDirectory=$DIR
ExecStart=$PY -m trendo.api
Restart=always
RestartSec=5
NoNewPrivileges=true
ProtectSystem=full
MemoryMax=1200M
[Install]
WantedBy=multi-user.target
EOF
# Główny blok strony należy do innych aplikacji. Własna trasa idzie wyłącznie do conf.d.
CF=/etc/caddy/Caddyfile
if ! grep -q 'conf.d' "$CF"; then echo "STOP: Caddyfile nie wczytuje conf.d. Nic nie zmieniam w Caddy."; exit 2; fi
TC=/etc/caddy/conf.d/trendo.caddy
printf 'handle_path /trendo-api/* {\n\treverse_proxy 127.0.0.1:%s\n}\n' "$PORT" > "$TC"
# Caddy działa na własnym koncie: plik musi być dla niego czytelny (jak pozostałe w conf.d).
chown --reference=/etc/caddy/Caddyfile "$TC"; chmod 644 "$TC"
if ! caddy validate --config "$CF" --adapter caddyfile >/dev/null 2>&1; then rm -f "$TC"; echo "STOP: Caddy nie przyjął trasy. Wycofałem ją, nic się nie zmieniło."; exit 2; fi
echo "Uruchamiam..."
systemctl daemon-reload
systemctl enable trendo >/dev/null 2>&1
systemctl restart trendo
if ! systemctl reload caddy; then
  rm -f "$TC"; systemctl reload caddy 2>/dev/null || true
  echo "STOP: Caddy nie przeładował konfiguracji. Wycofałem trasę Trendo, Twoje aplikacje działają jak wcześniej."
  journalctl -u caddy -n 3 --no-pager | cut -c1-200; exit 2
fi
sleep 6
if curl -fsS "https://$HOST/trendo-api/zdrowie" -o /tmp/trendo-zdrowie.json; then
  echo; echo "Status: OK"; cat /tmp/trendo-zdrowie.json; echo
  echo; echo "Kontrola jakości oceny na produktach wzorcowych (dwa przebiegi, 1–3 minuty)..."
  ( set -a; . /etc/trendo.env; set +a; cd "$DIR" && "$PY" -m trendo.kontrola ) || echo "Kontrola: błąd uruchomienia."
  systemctl restart trendo; sleep 6
  echo; echo "Próbne wyszukiwanie (koszula męska na wieczór, pierwsze może potrwać do 2 minut):"
  curl -fsS --max-time 200 "https://$HOST/trendo-api/szukaj?q=koszula&dzial=meskie&okazja=wieczor" | "$PY" -c "
import json,sys; d=json.load(sys.stdin)
[print(' ', s['nazwa'], '-', s['stan'], '-', s['ile'], 'produktów') for s in d['sklepy']]
print('  Ocena:', d.get('klasyfikacja'), '| pokazane:', len(d['produkty']), '| pominięte:', d.get('pominiete'), '| czas:', d.get('czas'), 's')
for p in d['produkty'][:8]: print('   +', p['sklep'], '-', p['nazwa'][:70])
" || echo "Próbne wyszukiwanie: brak odpowiedzi."
else
  echo "Status: BŁĄD, https://$HOST/trendo-api/zdrowie nie odpowiada."
  journalctl -u trendo -n 15 --no-pager
fi
echo; echo "Twoje pozostałe aplikacje:"
for u in "https://$HOST/smart-home-push/health" "https://planer.$HOST/" "https://dom.$HOST/" "https://$HOST/nav-tts/"; do
  echo "  $(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$u")  $u"
done
echo; echo "TRENDO GOTOWE"
}
main </dev/null
