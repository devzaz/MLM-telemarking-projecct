from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .models import MLMNode
from .serializers import MLMNodeSerializer
from django.views.decorators.http import require_POST
from django.db import transaction
from rest_framework.permissions import AllowAny

@login_required
def user_network_view(request):
    """
    Dashboard view for the currently logged-in user's network
    """
    try:
        node = request.user.mlmnode
    except MLMNode.DoesNotExist:
        node = None
    return render(request, 'mlm/user_network.html', {'node': node})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_node_detail(request, node_id):
    node = get_object_or_404(MLMNode, pk=node_id)
    serializer = MLMNodeSerializer(node)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @permission_classes([AllowAny])
def api_subtree(request, node_id):
    node = get_object_or_404(MLMNode, pk=node_id)
    # Small BFS to gather nodes up to depth 4 (safe default)
    max_depth = int(request.GET.get('depth', 4))
    result = []
    queue = [(node, 0)]
    while queue:
        cur, depth = queue.pop(0)
        result.append({
            'id': cur.id,
            'user': str(cur.user),
            'active': cur.active,
            'position': cur.position,
            'parent': cur.parent_id
        })
        if depth < max_depth:
            for c in cur.get_children():
                queue.append((c, depth + 1))
    return Response({'nodes': result})

@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_force_place(request):
    """
    Admin endpoint: create node for user and auto-place under provided start_node (optional)
    Payload: { "user_id": <id>, "start_node": <node_id|null> }
    """
    user_id = request.data.get('user_id')
    start_node_id = request.data.get('start_node')
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = get_object_or_404(User, pk=user_id)
    # create node
    with transaction.atomic():
        node_obj, created = MLMNode.objects.get_or_create(user=user, defaults={'active': False})
        if start_node_id:
            start_node = get_object_or_404(MLMNode, pk=start_node_id)
        else:
            start_node = None
        parent, pos = MLMNode.auto_place(node_obj, start_node=start_node)
    serializer = MLMNodeSerializer(node_obj)
    return Response({'placed': True, 'parent': getattr(parent, 'id', None), 'position': pos, 'node': serializer.data}, status=status.HTTP_201_CREATED)
