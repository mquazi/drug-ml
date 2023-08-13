(function(exports){
	var $datatable, DATA;
	var interested=[];
	
	var columnsList = [
	                   { data:"id","orderable": false}, 
	                   {data:"name"},
	                   {data:"type"},
	                   {data:"result"},
	                   {data:"endPoint"},
	                   {data:"domain"},
	                   {data:"group"}, 
	                   {data:"similarity.value"},
	                   {data:"similarity.neighborhoodActivity"},
	                   {data:"similarity.neighborhoodStructure","orderable": false}
	               ]; 
	
	var columnDefs = [ 
	                  {
	                	  targets:[0 ],
	                	  defaultContent:"", 
	                	  render: function ( data, type, row ){return '<input type="checkbox" class="editor-active">';},
	                	  //className: "dt-body-center"
	                  },
	                  {
	                	  targets:[1],
	                	  defaultContent:"", 
	                	  render: function ( data, type, row ){return '<a href="#" class="predx-model-name"  data-toggle="modal" data-target="#modelDetailModal" data-modelId="'+row.id+'">'+data+'</a>';}
	                  },
	                  {
	                	  targets:[5],
	                	  defaultContent:"", 
	                	  render: function ( data, type, row ) { 
	                		  var domain;
	                		  if(data >= 0.7){
	                			  domain = "high-confidence";
	                		  }else if(data >= 0.5){
	                			  domain = "medium-confidence";
	                		  }else{
	          		    		domain = "low-confidence";
	          		    	  }
	                		  return '<div class="'+domain+' all" title="'+domain+'">'+data+'</div>';
	                	} 
	                  },
	                  
	                  {
	                	  targets:[7],
	                	  defaultContent:"", 
	                	  render: function ( data, type, row ) {return Number(data).toFixed(2);} //similarity.value
	                  },
	                  {
	                	  targets:[ 9 ],
	                	  defaultContent:"",
	                	  //render:function(data, type, row){return '<span class="smiles" data-smiles="'+data+'"><i class="fa fa-picture-o" aria-hidden="true"></i></span>';}
	                	  render:function(data, type, row){return '<span class="smiles" data-smiles="'+data+'"><img src="image/structure.svg"></span>';}
	                  } ];
	
	function build(tableId,data){
		DATA=data;//for exporting
		if($datatable!=null){
			refresh(DATA);
			return;
		}
		
		$datatable = $("#"+tableId).DataTable({			
			"paging":false,
			"info":false,
			"order":[[7,"desc"],[1, "asc"]],//similarity & name
			searching:false,
			fixedHeader:true,
			scrollY:650,
			scrollX:true,
			scrollCollapse:true,
			scroller:true,
			responsive:true,
			columns:columnsList,
			columnDefs:columnDefs,
			data:DATA,
			"rowCallback": function( row, data, index ) {
				$(row).attr('id',data.id);
			},
			"drawCallback": function( settings ) { 
				var $predxTable=$('table.dataTable');//$("#"+tableId);
				//checkbox event
				registerCheckboxEvent($predxTable);
				
				//disable checkbox sorting
				$predxTable.find('thead tr th:first').removeClass().addClass('sorting_disabled');
				 
				//always put the interested models on top
				putInterestedOnTop($predxTable); 
 
				var $structimg=$("#structimg");//mouse hover, popup structure  
				//neighborhood structure 
				$('.smiles').hover(function(evt){ 
					var smi= $(this).attr('data-smiles');
					smi = smi.replace(/\%/g, "%25").replace(/\+/g, "%2B").replace(/\#/g, "%23");
					smi = smi.replace(/\[/g, "%5B").replace(/\]/g, "%5D");
					$structimg.parent().css({top:evt.pageY-220,left:evt.pageX-210}).show();   
				  	$structimg.attr('src',imgService+"?structure=" + smi+ "&size=200&apikey=5fd5bb2a05eb6195&standardize=true");  
				},function(){
					$structimg.parent().hide();
					$structimg.attr('src','image/loading.gif');
				}); 
		    }
		});
		  
		//When column header clicked(sort), also sort the interested.
		$('table.dataTable thead tr th').click(function (event) { 			
			if(interested.length<=0) return;
			
			var idx = $datatable.column(this).index();  
			var order= $(this).attr('class');
			//console.log(idx+'  '+order);
			sortInterestedByTHeaderClick(idx,order);
		}); 
		
		//export predx result
		$("#predx_export").click(function(event){ 
			 if (!window.Blob){
				 bootbox.alert('The File APIs are not fully supported in this browser.Please use modern browser like <a href="https://www.mozilla.org/en-US/firefox/new/" targer="_blank">FireFox</a> '+
				 'or <a href="https://www.google.com/chrome/" targer="_blank">Chrome</a>.');
				 return;
			 }
			var txtArr=[];
			txtArr.push('Activity Name\tPrediction Type\tPrediction Result\tApplicability Domain\tEnd Point\tSimilarity\tNeighbor Activity\tNeighbor Structure\n'); 
			
			$.each(DATA,function(i,d){
				txtArr.push(d.name+'\t'+d.type+'\t'+d.result+'\t'+d.domain+'\t'+d.endPoint+'\t'+d.similarity.value+'\t'+d.similarity.neighborhoodActivity+'\t'+d.similarity.neighborhoodStructure+'\n');
			});
			var blob = new Blob(txtArr, {type: "text/plain;charset=utf-8"});
			var suffix=new Date().toISOString().slice(0,10);
			saveAs(blob, 'predx-'+suffix +'.tsv');
		}); 
    }
	 
	//refresh with new data
	function refresh(data){
		$datatable.clear().rows.add(data).draw();
	}
	
	function putInterestedOnTop($predxTable){
		var id;
		for(var i=0;i<interested.length;i++){
			id=interested[i];
			var $tr=$("#"+id);
			$tr.addClass('hilit'); 
			$tr.find('td:first input[type="checkbox"]').prop('checked',true);
			$tr.insertBefore($predxTable.find('tbody tr:first'));  
		}
	}
	
	function sortInterestedByTHeaderClick(idx,order){ 
		 
		var $predxTable=$('table.dataTable');
		
		//interested rows
		var trs = $predxTable.find('tbody tr.hilit');
		
		var val, obj, arr=[];
			
		trs.each(function(i,tr){
			val = $(tr).find('td:nth-child('+(idx+1)+')').text();
			obj={};
			obj.val=val;
			obj.id=$(tr).attr('id');
			arr.push(obj)
		})
		   
		arr.sort(function(a,b) {return (a.val>b.val) ? (order=='sorting_desc'?1:-1):((b.val>a.val) ? (order=='sorting_desc'?-1:1):0);} ); 
		 
		interested=[];//!!!sorted
		$.each(arr,function(i,d){
			interested.push(d.id); 
		})
		
		putInterestedOnTop($predxTable);
	}
	
	function registerCheckboxEvent($predxTable){ 
		
		$('input[type="checkbox"]').change(function(){
			var $ckx=$(this);
			var $tr=$ckx.parent().parent();
			var modelId=$tr.attr('id');
			
			if($ckx.is(':checked')){  
				$tr.addClass('hilit'); 
				
				//unique
				if(interested.indexOf(modelId)<0)
					interested.push(modelId); 
				
				window.setTimeout( function(){
					$tr.insertBefore($predxTable.find('tbody tr:first'));  
				}, 150); 
			}else{
				$tr.removeClass('hilit');
				$tr.insertAfter($predxTable.find('tbody tr.hilit:last'));
				interested=$.grep(interested,function(val){
					return val!=modelId;//remove
				})
			} 
		})
	}
	
    exports.build=build;

})(typeof exports === 'undefined'? this.PredxTable = {}:exports);

