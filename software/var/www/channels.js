	$(document).ready(function(){
		readTemp();
		setInterval("readTemp();", 2000);	
	});
	
	function addChannel(){
		$( ".channel_template:first" ).children().clone().appendTo(".channel_index:last");
		$(".channel_index").children().last().addClass("temp_index");
		$(".channel_index").children().last().click(function () {
			showSetChannel(this.getElementsByClassName('chnumber')[0].innerHTML);
		});	
	}
	
	function removeChannel(){
		$(".channel_index").children().last().remove();
	}
	
	function readTemp(){
		if (updateActivated == 'true'){
				checkUpdateActivated();
		}else{
			loadJSON('channel', '', '3000', function (response) {
				jr = JSON.parse(response);				
				var channel_length = 0;
				for(var channels in jr.channels){
					for(var channel in jr.channels[channels]){
						channel_length++;
					}
				}
				while ($(".channel_index").children().length < channel_length) {
					addChannel();
				}
				while ($(".channel_index").children().length > channel_length) {
					removeChannel();
				}					
				
				var channel_index = 0;
				for(var channels in jr.channels){
					for(var channel in jr.channels[channels]){
						byClass("temp_index")[channel_index].getElementsByClassName('1-box channel')[0].style.borderColor = jr.channels[channels][channel].color;
						byClass("temp_index")[channel_index].getElementsByClassName('chtitle')[0].innerHTML = jr.channels[channels][channel].name;
						var chnumber = channel_index + 1;
						byClass("temp_index")[channel_index].getElementsByClassName('chnumber')[0].innerHTML = "#" + chnumber;
						byClass("temp_index")[channel_index].getElementsByClassName('tempmin')[0].innerHTML = getIcon('temp_down') + jr.channels[channels][channel].alert_low_limit + "°";
						byClass("temp_index")[channel_index].getElementsByClassName('tempmax')[0].innerHTML = getIcon('temp_up') + jr.channels[channels][channel].alert_high_limit + "°";
					if (jr.channels[channels][channel].value === null){
						byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].innerHTML = 'OFF';
						byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].style.color = "#FFFFFF";		
						byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].style.fontWeight = 'normal';
					}else{
						byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].innerHTML = jr.channels[channels][channel].value.toFixed(1) + "°";
						if (jr.channels[channels][channel].value < jr.channels[channels][channel].alert_low_limit){
							byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].style.color = "#1874cd";
							byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].style.fontWeight = 'bold';
						}else if (jr.channels[channels][channel].value > jr.channels[channels][channel].alert_high_limit){
							byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].style.color = "red";
							byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].style.fontWeight = 'bold';
						}else{
							byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].style.color = "#FFFFFF";
							byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].style.fontWeight = 'normal';
						}
					}						
						channel_index++;
					}
				}				
			})
		}
	}

	function showSetChannel(temp_channel){
        hideAll();
        showLoader('true');
        loadJSON('channel', '', '3000', function (response) {
            jr = JSON.parse(response);
            clearOption('sensor');
			loadJSON('api/colors/get', '', '3000', function (response) {
				color = JSON.parse(response);
				clearOption('color');
				for (var i = 0; i < color.length; i++) {
					byId('color').options[byId('color').options.length] = new Option(color[i]["0"], color[i]["1"]);
				}
				var channel_index = 0;
				for(var channels in jr.channels){
					for(var channel in jr.channels[channels]){
						if(temp_channel.substr(1, temp_channel.length-1) - 1 == channel_index){
							byId('channel_settings_headtitle').innerHTML  = jr.channels[channels][channel].name;
							byId('channel_name').value  = jr.channels[channels][channel].name;
							byId('temp_max').value  = jr.channels[channels][channel].alert_high_limit
							byId('temp_min').value  = jr.channels[channels][channel].alert_low_limit;						
							byId('color').value = jr.channels[channels][channel].color;
							byId('temp_alarm_high').checked = jr.channels[channels][channel].alert_high_enabled;
							byId('temp_alarm_low').checked = jr.channels[channels][channel].alert_low_enabled;
						}
						channel_index++;
					}
				}	
				byId('channel_settings').style.display = "inline";
				showLoader('false');				
				
				
			});	
        })
    }