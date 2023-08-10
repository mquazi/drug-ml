$.fn.extend({
    filedrop: function (options) {
        var defaults = {
            callback : null
        }
        options =  $.extend(defaults, options)
        return this.each(function() {
            var files = []
            var $this = $(this)

            // Stop default browser actions
            $this.bind('dragover dragleave', function(event) {
                event.stopPropagation()
                event.preventDefault()
            })

            // Catch drop event
            $this.bind('drop', function(event) {
                // Stop default browser actions
                event.stopPropagation()
                event.preventDefault()

                // Get all files that are dropped
                files = event.originalEvent.target.files || event.originalEvent.dataTransfer.files
                //console.log(files);
                // Convert uploaded file to data URL and pass through callback
                if(options.callback) {
                	
                	try{
                		var reader = new FileReader();
                        reader.onload = function(event) {
                            options.callback(event.target.result)
                        }
                        reader.readAsDataURL(files[0]);
                        
                	}catch(e) {
                	    alert("Error: seems File API is not supported on your browser"); 
                	} 
                }
                return false
            })
        })
    }
});