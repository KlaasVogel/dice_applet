<?php
declare(strict_types=1);

/**
 * Reverse proxy to vogel-api.duckdns.org.
 *
 * Forwards all requests from the browser (same-origin on klaasvogel.nl) to
 * the FastAPI backend, then streams the response back. Handles cookie
 * rewriting so the session cookie is bound to klaasvogel.nl instead of the
 * upstream domain.
 */

const UPSTREAM = 'https://vogel-api.duckdns.org';

// Strip the /api prefix from the request URI to get the upstream path.
$script_base  = rtrim(dirname($_SERVER['SCRIPT_NAME']), '/');
$request_path = strtok($_SERVER['REQUEST_URI'], '?');
$api_path     = substr($request_path, strlen($script_base)) ?: '/';
$query        = $_SERVER['QUERY_STRING'] ?? '';
$target       = UPSTREAM . $api_path . ($query !== '' ? '?' . $query : '');

// Forward browser request headers, skipping ones curl manages itself.
$headers = [];
foreach ($_SERVER as $key => $val) {
    if (!str_starts_with($key, 'HTTP_')) {
        continue;
    }
    $name = str_replace('_', '-', substr($key, 5));
    if (in_array($name, ['HOST', 'CONNECTION', 'ACCEPT-ENCODING'], true)) {
        continue;
    }
    $headers[] = "$name: $val";
}
if (isset($_SERVER['CONTENT_TYPE'])) {
    $headers[] = 'Content-Type: ' . $_SERVER['CONTENT_TYPE'];
}

$body   = file_get_contents('php://input');
$method = $_SERVER['REQUEST_METHOD'];

$ch = curl_init($target);
curl_setopt_array($ch, [
    CURLOPT_CUSTOMREQUEST  => $method,
    CURLOPT_HTTPHEADER     => $headers,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HEADER         => true,
    CURLOPT_ENCODING       => '',   // let curl decompress so content-length stays valid
    CURLOPT_FOLLOWLOCATION => false,
    CURLOPT_TIMEOUT        => 30,
]);

if ($body !== '' && in_array($method, ['POST', 'PUT', 'PATCH'], true)) {
    curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
}

$raw  = curl_exec($ch);
$info = curl_getinfo($ch);
curl_close($ch);

if ($raw === false) {
    http_response_code(502);
    header('Content-Type: application/json');
    echo '{"detail":"upstream unavailable"}';
    exit;
}

$resp_headers_raw = substr($raw, 0, $info['header_size']);
$resp_body        = substr($raw, $info['header_size']);

http_response_code((int) $info['http_code']);

// Headers we must not forward — either curl already handled them or they
// would confuse the browser after our decompression pass.
$skip_prefixes = [
    'transfer-encoding:',
    'connection:',
    'content-encoding:',
    'content-length:',
];

foreach (explode("\r\n", $resp_headers_raw) as $line) {
    if ($line === '' || str_starts_with($line, 'HTTP/')) {
        continue;
    }
    $lower = strtolower($line);
    foreach ($skip_prefixes as $prefix) {
        if (str_starts_with($lower, $prefix)) {
            continue 2;
        }
    }
    if (str_starts_with($lower, 'set-cookie:')) {
        // Remove Domain so the cookie is bound to klaasvogel.nl, not the upstream.
        $line = preg_replace('/;\s*domain=[^;]*/i', '', $line);
    }
    header($line, false);
}

echo $resp_body;
