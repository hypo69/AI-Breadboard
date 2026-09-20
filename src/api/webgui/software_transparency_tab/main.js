// Software Transparency Scanner script
// Frontend Controller
(function () {
  let allApps = [];
  let isScanning = false;

  async function initSoftwareTransparencyTab() {
    console.log('[TransparencyScanner] Initializing tab controller...');
    bindEvents();
    await loadScannerData(false);
  }

  function bindEvents() {
    const btnRefresh = document.getElementById('st-btn-refresh');
    if (btnRefresh) {
      btnRefresh.onclick = () => loadScannerData(true);
    }

    const searchInput = document.getElementById('st-search-input');
    if (searchInput) {
      searchInput.oninput = () => renderTable();
    }
  }

  async function loadScannerData(forceRefresh = false) {
    if (isScanning) return;
    isScanning = true;

    const badge = document.getElementById('st-status-badge');
    const tbody = document.getElementById('st-table-body');

    if (badge) {
      badge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-3 py-2';
      badge.innerText = 'â— Ð˜Ð´ÐµÑ‚ ÑÐ±Ð¾Ñ€ ÑÐ²ÐµÐ´ÐµÐ½Ð¸Ð¹ Ð¾ ÐŸÐž Ð¸ ÑÐµÑ‚Ð¸...';
    }

    if (tbody && (!allApps || allApps.length === 0)) {
      tbody.innerHTML = '|tr><td colspan="6" class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>Ð’Ñ‹Ð¿Ð¾Ð»Ð½ÑÐµÑ‚ÑÑ Ð¸Ð½Ð²ÐµÐ½Ñ‚Ð°Ñ€Ð¸Ð·Ð°Ñ†Ð¸Ñ ÑƒÑÑ‚Ð°Ð½Ð¾Ð²Ð»ÐµÐ½Ð½Ñ‹Ñ… Ñ›Ñ€Ð¾Ð³Ñ€Ð°Ð¼Ð¼, ÐºÐ¾Ð½Ñ„Ð¸Ð³ÑƒÑ€Ð°Ñ†Ð¸Ð¹ Ð¸ ÑÐµÑ‚ÐµÐ²Ñ‹Ñ… ÑÐ¾ÐºÐµÑ‚Ð¾Ð²...</td></tr>'.replace('|', '<');
    }

    try {
      const url = '/api/v1/software-scanner/scan?force_refresh=' + (forceRefresh ? 'true' : 'false');
      const res = await fetch(url);
      if (!res.ok) throw new Error('HTTP ' + res.status);

      const data = await res.json();
      allApps = data.apps || [];
      const summary = data.summary || {};

      document.getElementById('st-metric-total-apps').innerText = summary.total_apps || allApps.length;
      document.getElementById('st-metric-total-configs').innerText = summary.total_configs_found || 0;
      document.getElementById('st-metric-total-domains').innerText = summary.total_network_domains || 0;
      document.getElementById('st-metric-scan-duration').innerText = (summary.scan_duration_sec || 0) + ' Ñ.';

      if (badge) {
        badge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
        badge.innerText = 'à¥ÐžÐ±Ð½Ð°Ñ€ÑƒÐ¶ÐµÐ½Ð¾: ' + allApps.length + ' Ð¿Ñ€Ð¾Ð³Ñ€Ð°Ð¼Ð¼';
      }

      renderTable();
    } catch (err) {
      console.error('[TransparencyScanner] Scan error:', err);
      if (badge) {
        badge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-3 py-2';
        badge.innerText = 'â— ÐžÑˆÐ¸Ð±ÐºÐ° ÑÐºÐ°Ð½Ð¸Ñ€Ð¾Ð²Ð°Ð½Ð¸Ñ';
      }
      if (tbody) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger py-4">ÐžÑˆÐ¸Ð±ÐºÐ°: ' + err.message + '</td></tr>';
      }
    } finally {
      isScanning = false;
    }
  }

  function renderTable() {
    const tbody = document.getElementById('st-table-body');
    const searchInput = document.getElementById('st-search-input');
    const searchVal = (searchInput ? searchInput.value : '').toLowerCase().trim();

    if (!tbody) return;

    const filtered = allApps.filter((a) => {
      if (!searchVal) return true;
      return (
        a.name.toLowerCase().includes(searchVal) ||
        (a.publisher && a.publisher.toLowerCase().includes(searchVal)) ||
        (a.install_location && a.install_location.toLowerCase().includes(searchVal))
      );
    });

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">ÐÐ¸Ñ‡ÐµÐ³Ð¾ Ð½Ðµ Ð½Ð°Ð¹Ð´ÐµÐ½Ð¾ Ð¿Ð¾ Ñ„Ð¸Ð»ÑŒÑ‚Ñ€Ñƒ Â«' + searchVal + 'Â»</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map((app) => renderAppRow(app)).join('');‚ˆ›ÙKœ]Y\žTÙ[XÝÜ[
	ËœÝ]šY]ËXÛÛ™šYËX‰ÊK™›Ü‘XXÚ

ŠHOˆÂˆ‹›Û˜ÛXÚÈH

HOˆÂˆÛÛœÝ\YH‹™Ù]]šX]J	Ù]KX\ZY	ÊNÂˆÛÛœÝÙ™ÒYH\œÙR[
‹™Ù]]šX]J	Ù]KXÙ™ËZY	ÊKL
NÂˆÜ[ÛÛ™šYÓ[Ù[
\YÙ™ÒY
NÂˆNÂˆJNÂ‚ˆ›ÙKœ]Y\žTÙ[XÝÜ[
	ËœÝ\™\ÙX\˜ÚX‰ÊK™›Ü‘XXÚ

ŠHOˆÂˆ‹›Û˜ÛXÚÈH

HOˆÂˆÛÛœÝ\YH‹™Ù]]šX]J	Ù]KX\ZY	ÊNÂˆÜ[”™\ÙX\˜Ú[Ù[
\Y
NÂˆNÂˆJNÂˆB‚ˆ[˜Ý[Ûˆ™[™\\›ÝÊ\
HÂˆÛÛœÝÛÛ™šYÐ˜YÙ\ÈH
\˜ÛÛ™šY×Ùš[\È×JKœÛXÙJÊK›X\

ËY
HOˆÂˆ™]\›ˆ	Ï[œ]Ï‰ÈÈ	Ï]ÛˆÛ\ÜÏH˜ˆ‹[Ý][™K\ÙXÛÛ™\žH‹\ÛHKLLH›Û[[Û›ÜÜXÙHÛX[Ý]šY]ËXÛÛ™šYËXˆX‹LHYKLH^][˜Ø]HˆÝ[OH›X^]ÚYˆMÈˆ]KX\ZYH‰È
È\šY
È	Èˆ]KXÙ™ËZYH‰È
ÈY
È	Èˆ]OH‰È
ÈË™\Ü^WÜ]
È	È´+]IÈ
ÈË™š[[˜[YH
È	ÏØ]Û‰Èˆ	ÉÎÂˆJKš›Ú[Š	ÉÊNÂ‚ˆÛÛœÝ\˜YÙ\ÈH
\™]WÙ\™XÝÜšY\È×JKœÛXÙJÊK›X\


HOˆÂˆ™]\›ˆ	Ï]ˆÛ\ÜÏHœÛX[^][˜Ø]H^\ÙXÛÛ™\žHX‹LHˆ]OH‰È
È™\Ü^WÜ]
È	È
	È
È™\ØÜš\[Ûˆ
È	ÊH¼'äàHÜ[ˆÛ\ÜÏH^[YÚ‰È
È™\Ü^WÜ]
È	ÏÜÜ[Ù]‰ÎÂˆJKš›Ú[Š	ÉÊNÂ‚ˆÛÛœÝÛXZ[˜YÙ\ÈH
\›™]ÛÜš×Ù[™Ú[È×JKœÛXÙJÊK›X\

\
HOˆÂˆ™]\›ˆ	Ï]ˆÛ\ÜÏHœÛX[^][˜Ø]HX‹LHˆ]OH‰È
È\œ\œÜÙH
È	È¼'ã$Ü[ˆÛ\ÜÏH^Z[™›È‰È
È\™ÛXZ[—ÛÜ—Ú\
È	ÏÜÜ[ˆÜ[ˆÛ\ÜÏH^[]]YŽ‰È
È
\œÜÊH
È	ÏÜÜ[Ù]‰ÎÂˆJKš›Ú[Š	ÉÊNÂ‚ˆ]^˜Q\œÈH
\™]WÙ\™XÝÜšY\È×JK›[™ÝˆÈÈ	Ï]ˆÛ\ÜÏH^[]]YˆÝ[OH™›Û\Ú^™NˆÜ™[NÈŠÈ4-tbt-H	È
È
\™]WÙ\™XÝÜšY\Ë›[™ÝHÊH
È	È4.´,4`´,4.ô/´,ô/´,Ù]‰Èˆ	ÉÎÂˆ]^˜PÙ™ÜÈH
\˜ÛÛ™šY×Ùš[\È×JK›[™ÝˆÈÈ	Ï]ˆÛ\ÜÏH^[]]YˆÝ[OH™›Û\Ú^™NˆÜ™[NÈŠÈ4-tbt-H	È
È
\˜ÛÛ™šY×Ùš[\Ë›[™ÝHÊH
È	È4a4,4.t.ô/´,Ù]‰Èˆ	ÉÎÂˆ]^˜S™]ÈH
\›™]ÛÜš×Ù[™Ú[È×JK›[™ÝˆÈÈ	Ï]ˆÛ\ÜÏH^[]]YˆÝ[OH™›Û\Ú^™NˆÜ™[NÈŠÈ4-tbt-H	È
È
\›™]ÛÜš×Ù[™Ú[Ë›[™ÝHÊH
È	È4`ô-ô.ô/´,Ù]‰Èˆ	ÉÎÂ‚ˆ™]\›ˆ	Ï‰È
Âˆ	Ï]ˆÛ\ÜÏH™ËX›Û^]Ú]H‰È
È\ØØ\R[
\›˜[YJH
È	ÏÙ]]ˆÛ\ÜÏHœÛX[^[]]Y›Û[[Û›ÜÜXÙH^][˜Ø]HˆÝ[OH›X^]ÚYˆŒÈˆ]OH‰È
È
\š[œÝ[ÛØØ][Ûˆ	ÉÊH
È	È‰È
È\ØØ\R[
\š[œÝ[ÛØØ][Ûˆ\™^XÝ]X›WÜ]	ô(t.4`t`´-t/4/tbô.H4.´/´/4/ô/´/t-t/t`‰ÊH
È	ÏÙ]Ý‰È
Âˆ	Ï]ˆÛ\ÜÏHœÛX[^[YÚ‰È
È\ØØ\R[
\œX›\Ú\ˆ	ô't-t.4-ô,´-t`t`´-t/IÊH
È	ÏÙ]Ü[ˆÛ\ÜÏH˜˜YÙH™Ë\ÙXÛÛ™\žH™Ë[ÜXÚ]KLH^Z[™›È›Û[[Û›ÜÜXÙHÛX[‰È
È\ØØ\R[
\™\œÚ[ÛŠH
È	ÏÜÜ[ˆÜ[ˆÛ\ÜÏH˜˜YÙH™Ë\ÙXÛÛ™\žH™Ë[ÜXÚ]KLH^\ÙXÛÛ™\žH›Û[[Û›ÜÜXÙHÛX[‰È
È\˜\˜Ú]XÝ\™H
È	ÏÜÜ[Ý‰È
Âˆ	Ï‰È
È
\˜YÙ\È	ÏÜ[ˆÛ\ÜÏH^[]]YÛX[´'t-H4/´,t/t,4`4`ô-´-t/tbÏÜÜ[‰ÊH
È^˜Q\œÈ
È	ÏÝ‰È
Âˆ	Ï‰È
È
ÛÛ™šYÐ˜YÙ\È	ÏÜ[ˆÛ\ÜÏH^[]]YÛX[´'t-t`ˆ4a4,4.t.ô/´,ÜÜ[‰ÊH
È^˜PÙ™ÜÈ
È	ÏÝ‰È
Âˆ	Ï‰È
È
ÛXZ[˜YÙ\È	ÏÜ[ˆÛ\ÜÏH^[]]YÛX[´&ô/´.´,4.ôc4/tbô.H4`4-t-´.4/ÜÜ[‰ÊH
È^˜S™]È
È	ÏÝ‰È
Âˆ	ÏÝ[OH^X[YÛŽˆšYÚÈ]ÛˆÛ\ÜÏH˜ˆ‹\ÛH‹[Ý][™KZ[™›ÈÝ\™\ÙX\˜ÚXˆˆ]KX\ZYH‰È
È\šY
È	Èˆ]OHRH4.4`t`t.ô-t-4/´,´,4/t.4-H4/ô`4/´,ô`4,4/4/4bÈHÛ\ÜÏH˜šHšK\›Ø›ÝÚOˆ4&4`t`t.ô-t-4/´,´,4`´cØ]ÛÝ‰È
Âˆ	ÏÝ‰ÎÂˆB‚ˆ[˜Ý[ÛˆÜ[ÛÛ™šYÓ[Ù[
\YÙ™ÒY
HÂˆÛÛœÝ\H[\Ë™š[™

JHOˆKšYOOH\Y
NÂˆYˆ
X\X\˜ÛÛ™šY×Ùš[\ÈX\˜ÛÛ™šY×Ùš[\ÖØÙ™ÒYJH™]\›ŽÂ‚ˆÛÛœÝÙ™ÈH\˜ÛÛ™šY×Ùš[\ÖØÙ™ÒYNÂˆØÝ[Y[™Ù][[Y[žRY
	ÜÝXÛÛ™šYË[[Ù[]]IÊKš[›™\•^H	ô&´/´/ut.4,ô`ô`4,4a´.4cÎˆ	È
ÈÙ™Ë™š[[˜[YNÂˆØÝ[Y[™Ù][[Y[žRY
	ÜÝXÛÛ™šYË[[Ù[\]	ÊKš[›™\•^H	ô'ô`ô`´cˆ	È
ÈÙ™Ë™\Ü^WÜ]
È	È
	È
ÈÙ™Ë™›Ü›X]Õ\\Ø\ÙJ
H
È	Ë	È
ÈÙ™ËœÚ^™WØž]\È
È	È4,t,4.tJIÎÂˆØÝ[Y[™Ù][[Y[žRY
	ÜÝXÛÛ™šYË[[Ù[XÛÛ[	ÊK^ÛÛ[HÙ™ËœØ[\WØÛÛ[	ËËÈ4(t/´-4-t`4-´.4/4/´-H4/ô`ô`t`´/ˆ4.4.ô.4/t-t-4/´`t`´`ô/ô/t/‰ÎÂ‚ˆÛÛœÝ[Ù[H™]È›ÛÝÝ˜\“[Ù[
ØÝ[Y[™Ù][[Y[žRY
	ÜÝXÛÛ™šYË[[Ù[	ÊJNÂˆ[Ù[œÚÝÊ
NÂˆB‚ˆ\Þ[˜È[˜Ý[ÛˆÜ[”™\ÙX\˜Ú[Ù[
\Y
HÂˆÛÛœÝ\H[\Ë™š[™

JHOˆKšYOOH\Y
NÂˆYˆ
X\
H™]\›ŽÂ‚ˆØÝ[Y[™Ù][[Y[žRY
	ÜÝ\™\ÙX\˜Ú[[Ù[]]IÊKš[›™\•^H	ÐRH4&4`t`t.ô-t-4/´,´,4/t.4-Nˆ	È
È\›˜[YNÂˆÛÛœÝ›ÙHHØÝ[Y[™Ù][[Y[žRY
	ÜÝ\™\ÙX\˜Ú[[Ù[X›ÙIÊNÂˆ›ÙKš[›™\’SH	Ï]ˆÛ\ÜÏH^XÙ[\ˆKM]ˆÛ\ÜÏHœÜ[›™\‹X›Ü™\ˆÜ[›™\‹X›Ü™\‹\ÛH^Z[™›ÈYKLˆÙ]‘Ù[Z[šH4,4/t,4.ô.4-ô.4`4`ô-t`ˆ4/t,4-ô/t,4aô-t/t.4-H4/ô`4/´,ô`4,4/4/4bÈ4.4/ô`4/´,´-t`4cô-t`ˆ4-4/´.´`ô/4-t/t`´,4a´.4c‹‹‹Ù]‰ÎÂ‚ˆÛÛœÝ[Ù[H™]È›ÛÝÝ˜\“[Ù[
ØÝ[Y[™Ù][[Y[žRY
	ÜÝ\™\ÙX\˜Ú[[Ù[	ÊJNÂˆ[Ù[œÚÝÊ
NÂ‚ˆžHÂˆÛÛœÝ™\ÈH]ØZ]™]Ú
	ËØ\KÝŒKÜÛÙØ\™K\ØØ[›™\‹Ü™\ÙX\˜Ú	ËÂˆY]Ùˆ	ÔÔÕ	ËˆXY\œÎˆÈ	ÐÛÛ[U\IÎˆ	Ø\XØ][Û‹ÚœÛÛ‰ÈKˆ›ÙNˆ”ÓÓ‹œÝš[™ÚYžJÈ\ÚYˆ\Y›Ü˜ÙWÜ™Yœ™\Úˆ˜[ÙHJKˆJNÂ‚ˆYˆ
\™\Ë›ÚÊH›ÝÈ™]È\œ›ÜŠ	Ò	È
È™\ËœÝ]\ÊNÂˆÛÛœÝ]HH]ØZ]™\ËšœÛÛŠ
NÂ‚ˆÛÛœÝÛÛ™‘˜XÝÈH
]K˜ÛÛ™š\›YYÙ˜XÝÈ×JK›X\

ŠHOˆ	ÏO‰È
È\ØØ\R[
ŠH
È	ÏÛO‰ÊKš›Ú[Š	ÉÊH	ÏO´'t-H4-ô,4a4.4:ÑÐ¸Ñ€Ð¾Ð²Ð°Ð½Ð¿</li>';
      const inferFacts = (data.inferred_facts || []).map((f) => '<li>' + escapeHtml(f) + '</li>').join('') || '<li>ÐÐµÑ‚ Ð¿Ñ€ÐµÐ´Ð¿Ð¾Ð»Ð¾Ð¶ÐµÐ½Ð¸Ð¹</li>';

      body.innerHTML = '<div class="mb-3"><h6 class="text-info fw-bold mb-1">ðŸ“ˆ ÐÐ°Ð·Ð½Ð°Ñ‡ÐµÐ½Ð¸Ðµ Ð¿Ñ€Ð¾Ð³Ñ€Ð°Ð¼Ð¼Ñ‹</h6><p class="small text-light mb-2">' + escapeHtml(data.summary) + '</p></div>' +
        '<div class="mb-3"><h6 class="text-warning fw-bold mb-1">Indicatorâš ÐÐ°Ð·Ð½Ð°Ñ‡ÐµÐ½Ð¸Ðµ ÐºÐ¾Ð½Ñ„Ð¸Ð³ÑƒÑ€Ð°Ñ†Ð¸Ð¹</h6><p class="small text-light mb-2">' + escapeHtml(data.config_purpose_explanation || 'Ð¡Ñ‚Ð°Ð½Ð´Ð°Ñ€Ñ‚Ð½Ñ‹Ðµ Ð½Ð°ÑÑ‚Ñ€Ð¾Ð¹ÐºÐ¸ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»Ñ.') + '</p></div>' +
        '<div class="mb-3"><h6 class="text-primary fw-bold mb-1">ðŸ’¾ Ð“Ð´Ðµ Ð¸ ÐºÐ°ÐºÐ¸Ðµ Ð´Ð°Ð½Ð½Ñ‹Ðµ ÑÐ¾Ñ…Ñ€Ð°Ð½ÑÑŽÑ‚ÑÑ?</h6><p class="small text-light mb-2">' + escapeHtml(data.data_storage_explanation || 'Ð›Ð¾ÐºÐ°Ð»ÑŒÐ½Ñ‹Ðµ Ñ„Ð°Ð¹Ð»Ñ‹ Ð² ÐºÐ°Ñ‚Ð°Ð»Ð¾Ð³Ð°Ñ… AppData.') + '</p></div>' +
        '<div class="mb-3"><h6 class="text-success fw-bold mb-1">ðŸ˜ Ð¡ÐµÑ‚ÐµÐ²Ð°Ñ Ð°ÐºÑ‚Ð¸Ð²Ð½Ð¾ÑÑ‚ÑŒ Ð¸ Ð´Ð¾Ð¼ÐµÐ½Ñ‹</h6><p class="small text-light mb-2">' + escapeHtml(data.network_activity_explanation || 'ÐŸÐµÑ€Ð¸Ð¾Ð´Ð¸Ñ‡ÐµÑÐºÐ°Ñ Ð¿Ñ€Ð¾Ð²ÐµÑ€ÐºÐ° Ð¾Ð±Ð½Ð¾Ð²Ð»ÐµÐ½Ð¸Ð¹.') + '</p></div>' +
        '<div class="row g-2 mt-2 pt-2 border-top border-secondary">' +
        '<div class="col-md-6"><h6 class="text-success small fw-bold">ÐŸÐ¾Ð´Ñ‚Ð²ÐµÑ€Ð¶Ð´ÐµÐ½Ð½Ñ‹Ðµ Ñ„Ð°ÐºÑ‚Ñ‹</h6><ul class="small text-muted ps-3 mb-2">' + confFacts + '</ul></div>' +
        '<div class="col-md-6"><h6 class="text-warning small fw-bold">ÐŸÑ€ÐµÐ´Ð¿Ð¾Ð»Ð¾Ð¶ÐµÐ½Ð¸Ñ Ð¼Ð¾Ð´ÐµÐ»Ð¸:</h6><ul class="small text-muted ps-3 mb-2">' + inferFacts + '</ul></div>' +
        '</div>';
    } catch (err) {
      body.innerHTML = '<div class="alert alert-danger small">ÐžÑˆÐ¸Ð±ÐºÐ° AIÀ¸ÑÑÐ»ÐµÐ´Ð¾Ð²Ð°Ð½Ð¸Ñ: ' + err.message + '</div>';
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  window.initSoftwareTransparencyTab = initSoftwareTransparencyTab;
è})();
