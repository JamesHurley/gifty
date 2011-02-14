/**
 * @author kathrynbrisbin
 */

var parentLocation;

function addText() {
	var windowLocation = window.location.href;
	var params = windowLocation.split('#gifty?')[1];
	var subparams = params.split('&gifty');
	var title = unescape(subparams[0].split('=',2)[1]);
	parentLocation = subparams[1].substring(subparams[1].indexOf('=')+1,subparams[1].length);
	document.getElementById('_giftDescription').value = title;
	document.getElementById('_giftLink').value = parentLocation;
}

function submitForm() {
	
	$.post("/bookmarklet", $("#frameform").serialize());
	
	closeBox("close");
}

function closeBox(message) {
	var url = parentLocation + "#gifty=" + message;
	try {
		top.location.replace(url);
	} catch (e) {
		top.location = url;
	}
}

function homepage() {
	var url = "https://www.google.com/accounts/ServiceLogin?service=ah&continue=http://dev.latest.giftyapp.appspot.com/_ah/login%3Fcontinue%3Dhttp://dev.latest.giftyapp.appspot.com/&ltmpl=gm&ahname=Gifty&sig=0082dc52a7690b7a313d3b8c88368010"									 
	try {
		top.location.href=url;
	} catch (e) {
		top.location.href=url;
	}
}