/**
 * @author kathrynbrisbin
 */

var giftyFunctions = function(){
	
	//code from friendfeed javascript, sets the location of the iframe
	function giftySetIframe(){
		var iframe;
		
		if (navigator.userAgent.indexOf("Safari") != -1) {
			iframe = frames["giftyframe"];
		}
		else {
			iframe = document.getElementById("giftyframe").contentWindow;
		}
		
		if (!iframe) 
			return;
		
		var url = 'http://www.giftyapp.com/bookmarklet'
		url += '#gifty?giftname=' + document.title;
		url += '&giftylocation=' + window.location.href;
		try {
			iframe.location.replace(url);
		} 
		catch (e) {
			iframe.location = url; // safari
		}
	}
	
	//check for a change in the URL
	function giftyFrameMessage(){
		var gCurScroll = giftyScrollPos();
		var hash = location.href.split('#');
		if (hash.length > 1 && hash[hash.length - 1].match('gifty') != null) {
			location.replace(hash[0] + "#");
			giftySetScroll(gCurScroll);
			giftyHandleMessage(hash[hash.length - 1]);
		}
	}
	
	//from friendfeed javascript
	//find the location of the scroll
	function giftyScrollPos(){
		if (self.pageYOffset !== undefined) {
			return {
				x: self.pageXOffset,
				y: self.pageYOffset
			};
		}
	}
	
	//get the scroll position
	//from friendfeed javascript
	function giftySetScroll(pos){
		var e = document.documentElement, b = document.body;
		e.scrollLeft = b.scrollLeft = pos.x;
		e.scrollTop = b.scrollTop = pos.y;
	}
	
	//show the message from the iframe
	function giftyHandleMessage(msg){
		giftyClose();
	}
	
	//close the box
	function giftyClose(){
		var giftybox = document.getElementById('giftybox');
		giftybox.parentNode.removeChild(giftybox);
		window.onscroll = null;
	}
	
	return {
		addGiftyDiv: function(){
			var container = document.createElement("div");
			container.style.padding = "0";
			container.style.margin = "0";
			container.style.border = "1px solid";
			container.id = "giftybox";
			container.style.position = "absolute";
			container.style.top = giftyScrollPos().y + "px";
			container.style.right = "0";
			container.style.zIndex = 100000;
			container.style.width = "350px";
			container.style.height = "210px";
			container.style.backgroundColor = "white";
			container.innerHTML = '<iframe style="width:100%;height:100%;border:0px;" id="giftyframe"></iframe>';
			document.body.appendChild(container);
			
			
			//set up message checking to run every so often
			var interval = window.setInterval(function(){
				giftyFrameMessage();
			}, 50);
			
			giftySetIframe();
			//when the window scrolls, change the location of the box
			window.onscroll = function(){
				document.getElementById('giftybox').style.top = giftyScrollPos().y + "px";
			};
		}
	}
}

giftyFunctions().addGiftyDiv();




