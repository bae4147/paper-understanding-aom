
document.addEventListener('DOMContentLoaded',function(){var start=new Date();var doiMeta=document.querySelector('meta[name="publication_doi"]');if(doiMeta){var doi=doiMeta.getAttribute('content');var actionUrl='/action/analytics';function sendEvent(data){if(navigator.sendBeacon){navigator.sendBeacon(actionUrl,data);}else{var xhr=new XMLHttpRequest();xhr.open('POST',actionUrl,true);xhr.send(data);}}
window.addEventListener('beforeunload',function(){var data=new FormData();var end=new Date();var duration=end-start;data.append('DOI',doi);data.append('EventType','FullTextDuration');data.append('Duration',duration);sendEvent(data);});window.addEventListener('afterprint',function(){var data=new FormData();data.append('DOI',doi);data.append('EventType','FullTextPrint');sendEvent(data);});}});

