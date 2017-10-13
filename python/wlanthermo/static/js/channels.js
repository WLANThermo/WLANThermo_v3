	var channels_api = "api/channels"; // API der Kanäle
	var colors_api = "api/colors"; // API der verfügbaren Farben
	var refreshInterval = "2000"; // Refresh Intervall in ms der Temp Werte
	var getTimeout = "3000"; // Timeout der get API's
	
	$(document).ready(function(){
		readTemp();
		setInterval("readTemp();", refreshInterval);	
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
		} else {
			$.getJSON(channels_api, function (response) {
				var channel_length = 0;
				for(var channels in response){
					for(var channel in response[channels]){
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
				for(var channels in response){
					for(var channel in response[channels]){
						byClass("temp_index")[channel_index].getElementsByClassName('1-box channel')[0].style.borderColor = response[channels][channel].color;
						byClass("temp_index")[channel_index].getElementsByClassName('chtitle')[0].innerHTML = response[channels][channel].name;
						var chnumber = channel_index + 1;
						byClass("temp_index")[channel_index].getElementsByClassName('chnumber')[0].innerHTML = "#" + chnumber;
						byClass("temp_index")[channel_index].getElementsByClassName('tempmin')[0].innerHTML = getIcon('temp_down') + response[channels][channel].alert_low_limit + "°";
						byClass("temp_index")[channel_index].getElementsByClassName('tempmax')[0].innerHTML = getIcon('temp_up') + response[channels][channel].alert_high_limit + "°";
					if (response[channels][channel].value === null){
						byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].innerHTML = 'OFF';
						byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].style.color = "#FFFFFF";		
						byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].style.fontWeight = 'normal';
					}else{
						byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].innerHTML = response[channels][channel].value.toFixed(1) + "°";
						if (response[channels][channel].value < response[channels][channel].alert_low_limit){
							byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].style.color = "#1874cd";
							byClass("temp_index")[channel_index].getElementsByClassName('temp')[0].style.fontWeight = 'bold';
						}else if (response[channels][channel].value > response[channels][channel].alert_high_limit){
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
        $.getJSON(channels_api, function (channels) {
            clearOption('sensor');
			$.getJSON(colors_api, function (color) {
				clearOption('color');
				for (var i = 0; i < color.length; i++) {
					byId('color').options[byId('color').options.length] = new Option(color[i]["0"], color[i]["1"]);
				}
				var channel_index = 0;
				for(var channels in channels){
					for(var channel in channels[channels]){
						if(temp_channel.substr(1, temp_channel.length-1) - 1 == channel_index){
							modules = channels;
							ch = channel;
							getJSON("api/modules/" + modules +"/sensors", function (sensors) {
								clearOption('sensor');
								for (var i = 0; i < sensors.length; i++) {
									byId('sensor').options[byId('sensor').options.length] = new Option(sensors[i], sensors[i]);
								}
								byId('sensor').value  = channels[modules][ch].sensor_type;
								byId('channel_settings_headtitle').innerHTML  = channels[modules][ch].name;
								byId('channel_name').value  = channels[modules][ch].name;
								byId('temp_max').value  = channels[modules][ch].alert_high_limit
								byId('temp_min').value  = channels[modules][ch].alert_low_limit;
								byId('color').value = channels[modules][ch].color;
								byId('temp_alarm_high').checked = channels[modules][ch].alert_high_enabled;
								byId('temp_alarm_low').checked = channels[modules][ch].alert_low_enabled;
								delete modules;
								delete ch;
							});
						}
						channel_index++;
					}
				}	
				byId('channel_settings').style.display = "inline";
				showLoader('false');						
			});	
        })
    }
	