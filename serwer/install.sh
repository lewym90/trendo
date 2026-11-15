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
[ -f /etc/trendo.env ] || ( umask 077; printf 'PORT=%s\nTRENDO_DANE=/var/lib/trendo\n' "$PORT" > /etc/trendo.env )
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
  echo; echo "Kontrola jakości oceny (zwykle bez kosztów na zapisanych odpowiedziach modelu; płatna tylko po zmianie polecenia AI albo modelu)..."
  ( set -a; . /etc/trendo.env; set +a; cd "$DIR" && "$PY" -m trendo.kontrola ) || echo "Kontrola: błąd uruchomienia."
  echo; echo "Trendy: czytam źródła (Lyst, Tagwalk, WGSN, Heuritech, Vogue, Elle, Glamour i inne; pierwszy raz kilka minut)..."
  ( set -a; . /etc/trendo.env; set +a; cd "$DIR" && timeout 1500 "$PY" -m trendo.trendy ) || echo "Trendy: błąd uruchomienia."
  echo; echo "Znaki sklepów: prawdziwe logo z nagłówka strony sklepu (próba na 5 sklepach, reszta pobierze się sama w tle)..."
  ( set -a; . /etc/trendo.env; set +a; cd "$DIR" && timeout 400 "$PY" -m trendo.logo Reserved Zara "H&M" Zalando Sinsay ) || echo "Znaki sklepów: błąd uruchomienia."
  systemctl restart trendo; sleep 6
  echo; echo "Sklepy podłączone bezpośrednio (próba: sukienka w damskich, koszula w męskich; gdy sklep ich nie ma — buty):"
  ( set -a; . /etc/trendo.env; set +a; cd "$DIR" && timeout 300 "$PY" - <<'PYEOF'
from trendo import lacznik_strony as L, lacznik_zara, lacznik_lpp, lacznik_modivo, lacznik_przegladarka, lacznik_ccc, lacznik_wittchen
from collections import Counter
wyn = {}
for dz, q in (("damskie", "sukienka"), ("meskie", "koszula")):
    for l in (lacznik_zara, lacznik_lpp, lacznik_modivo, lacznik_przegladarka, lacznik_ccc, lacznik_wittchen):
        try:
            lista, stan = l.szukaj(q, dz)
        except Exception as e:
            lista, stan = [], "błąd " + str(e)[:40]
        ile = Counter(p["sklep"] for p in lista)
        for sk, n in ile.items():
            wyn.setdefault(sk, {})[dz] = n
        brak = [sk for sk in getattr(l, "SKLEPY", [l.NAZWA]) if sk not in ile and not (dz == "meskie" and sk == "Mohito")]
        if brak and stan == "ok":  # sklep bez tej rzeczy (np. obuwniczy): próba na butach
            buty = "botki" if dz == "damskie" else "sneakersy"
            try:
                lista2, _ = l.szukaj(buty, dz)
            except Exception:
                lista2 = []
            ile2 = Counter(p["sklep"] for p in lista2)
            for sk in brak:
                wyn.setdefault(sk, {})[dz] = f"{ile2[sk]} ({buty})" if ile2.get(sk) else 0
        elif not lista:
            wyn.setdefault(l.NAZWA, {})[dz] = stan
    for k in L.SKLEPY_KONF:
        sk, lista, stan = L._sklep((k, q, dz))
        if stan == "ok" and not lista:  # sklep bez tej rzeczy (np. obuwniczy): próba na butach
            buty = "botki" if dz == "damskie" else "sneakersy"
            _, lista2, stan2 = L._sklep((k, buty, dz))
            if stan2 == "ok" and lista2:
                wyn.setdefault(sk, {})[dz] = f"{len(lista2)} ({buty})"
                continue
        if stan != "pomijam":
            wyn.setdefault(sk, {})[dz] = len(lista) if stan == "ok" else stan
for sk in sorted(wyn, key=str.lower):
    d = wyn[sk]
    print(f"  {sk:12} damskie: {str(d.get('damskie', '-')):12}  męskie: {d.get('meskie', '-')}")
PYEOF
  ) || echo "Sklepy: błąd uruchomienia."
  echo; echo "Próbne wyszukiwanie przez serwer (koszula męska; pierwsze może potrwać do 2 minut):"
  curl -fsS --max-time 200 "https://$HOST/trendo-api/szukaj?q=koszula&dzial=meskie" -o /tmp/trendo-szukaj.json && "$PY" -c "
import json; d=json.load(open('/tmp/trendo-szukaj.json'))
[print(' ', s['nazwa'], '-', s['stan'], '-', s['ile'], 'produktów') for s in d['sklepy']]
P=d['produkty']; w=[p for p in P if 'wieczor' in (p.get('okazje') or [])]
print('  Ocena:', d.get('klasyfikacja'), '| wszystkie:', len(P), '| pasuje na wieczór:', len(w), '| bez oceny:', sum(p.get('okazje') is None for p in P), '| czas:', d.get('czas'), 's')
" || echo "Próbne wyszukiwanie: brak odpowiedzi."
  echo; echo "Próbne wyszukiwanie damskie (sukienka; zasila też damskie okazje dnia):"
  curl -fsS --max-time 200 "https://$HOST/trendo-api/szukaj?q=sukienka&dzial=damskie" | "$PY" -c "
import json,sys; d=json.load(sys.stdin); P=d['produkty']
print('  Sklepów z wynikami:', sum(1 for s in d['sklepy'] if s['ile']), '| produktów:', len(P), '| czas:', d.get('czas'), 's')
" || echo "Próbne wyszukiwanie damskie: brak odpowiedzi."
  echo; echo "Okazje dnia (tylko obniżki sprawdzone, rosną z każdym wyszukiwaniem i nocnym przeglądem sklepów):"
  for dz in damskie meskie; do curl -fsS --max-time 30 "https://$HOST/trendo-api/okazje?dzial=$dz" | "$PY" -c "
import json,sys; d=json.load(sys.stdin); o=d['okazje']
print('  $dz:', len(o), 'okazji' + (', np. ' + ', '.join(f\"{x['sklep']} −{x['rabat']}%\" for x in o[:3]) if o else ''))
" || echo "  $dz: brak odpowiedzi"; done
  echo; echo "Szukanie ze zdjęcia (próba na zdjęciu produktu z wyników):"
  FOTO=$("$PY" -c "import json; P=json.load(open('/tmp/trendo-szukaj.json'))['produkty']; print(next((p['zdjecie'] for p in P if p.get('zdjecie','').startswith('http') and p['sklep'] in ('Zara','Reserved','House','Modivo')), ''))" 2>/dev/null)
  if [ -n "$FOTO" ] && curl -fsSL --max-time 30 -A "Mozilla/5.0" "$FOTO" -o /tmp/trendo-foto.jpg; then
    curl -sS --max-time 90 -X POST -H "Content-Type: image/jpeg" --data-binary @/tmp/trendo-foto.jpg "https://$HOST/trendo-api/zdjecie" | "$PY" -c "
import json,sys; d=json.load(sys.stdin); print('  Rozpoznane hasło:', d.get('q') or d.get('blad'))"
  else echo "  Nie udało się pobrać zdjęcia próbnego (to nie błąd aplikacji)."; fi
  rm -f /tmp/trendo-szukaj.json /tmp/trendo-foto.jpg
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
