$(document).ready(function() {
   $('.flip-modal-trigger').click(function(c) {
        c.preventDefault();
        h = this.href; 
        $('#auth-mod').modal('show').find('.modal-body').empty().html(
            '<iframe class="flip-iframe" src="'+h+'"></iframe>'
        ); 
    });


});
