
WebView myWebView = (WebView) findViewById(R.id.webview);
myWebView.getSettings().setJavaScriptEnabled(true);
// Charger l'adresse locale de votre serveur Flask embarqué ou de votre page principale
myWebView.loadUrl("http://10.0.2.2:5000/");
