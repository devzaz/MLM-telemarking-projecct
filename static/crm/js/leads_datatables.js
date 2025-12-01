// crm/static/crm/js/leads_datatables.js
document.addEventListener('DOMContentLoaded', function () {
  const table = $('#leads-table').DataTable({
    ajax: {
      url: '/crm/api/leads/',
      data: function (d) {
        d.status = $('#filter-status').val();
        d.assigned = $('#filter-assigned').val();
      }
    },
    columns: [
      { data: 'id', width: '6%' },
      { data: 'name' },
      { data: 'email' },
      { data: 'phone' },
      { data: 'status', width: '12%' },
      { data: 'assigned_to', width: '12%' },
      { data: 'created_at', width: '12%' },
      { data: 'actions', orderable: false, searchable: false, width: '20%' }
    ],
    pageLength: 25,
    processing: true,
    serverSide: false, // we use a simple server slice above; set true if you implement full server protocol
    drawCallback: function () {
      // re-attach any dynamic handlers if needed
    }
  });

  $('#filter-status,#filter-assigned').on('change', function () {
    table.ajax.reload();
  });
});
