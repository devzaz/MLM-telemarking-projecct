from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class MLMNode(models.Model):
    POSITION_CHOICES = (('L', 'Left'), ('R', 'Right'))

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mlmnode')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    position = models.CharField(max_length=1, choices=POSITION_CHOICES, null=True, blank=True)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['active']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"MLMNode(user={self.user}, pos={self.position}, parent={self.parent_id})"

    def clean(self):
        # Ensure position is consistent with parent: parent can't have more than two children
        if self.parent:
            siblings = self.parent.children.exclude(pk=self.pk)
            if siblings.count() >= 2:
                raise ValidationError("Parent already has two children.")

            # Ensure position is not duplicate
            if siblings.filter(position=self.position).exists():
                raise ValidationError(f"Position {self.position} is already taken under this parent.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_children(self):
        return self.children.all()

    def get_upline(self, levels=None):
        """Return upline nodes up to `levels` (None => all)"""
        upline = []
        node = self.parent
        while node and (levels is None or len(upline) < levels):
            upline.append(node)
            node = node.parent
        return upline

    def get_downline(self, levels=1):
        """BFS downline up to `levels`"""
        nodes = []
        queue = [(self, 0)]
        while queue:
            node, depth = queue.pop(0)
            if depth == 0:
                pass
            else:
                nodes.append((node, depth))
            if depth < levels:
                for c in node.get_children():
                    queue.append((c, depth + 1))
        return nodes

    @classmethod
    def auto_place(cls, new_user_node, start_node=None):
        """
        Auto placement algorithm (fixed):
        - Breadth-first traverse from start_node (or root candidates) to find first node with available child slot.
        - Place in left first then right.
        - Never consider `new_user_node` itself as a candidate parent (prevents self-parenting).
        - Returns (parent_node_or_None, position_or_None).
        """
        # If the node is not saved yet, it has no pk; that's fine.
        new_pk = getattr(new_user_node, 'pk', None)

        if start_node is None:
            # find root candidates (nodes with no parent) ordered by created_at,
            # but exclude the node being placed (if it already exists in DB).
            qs = cls.objects.filter(parent__isnull=True).order_by('created_at')
            if new_pk is not None:
                qs = qs.exclude(pk=new_pk)
            candidates = qs
            if not candidates.exists():
                # If no other nodes exist, place as root (no parent, position null)
                new_user_node.parent = None
                new_user_node.position = None
                new_user_node.save()
                return None, None
            start_node = candidates.first()

        # BFS over tree, but never treat node equal to new_user_node as parent
        queue = [start_node]
        visited = set()
        while queue:
            node = queue.pop(0)
            if node.pk == new_pk:
                # skip the node if it's the same as the node we're placing
                continue
            # guard against accidental cycles
            if node.pk in visited:
                continue
            visited.add(node.pk)

            children = list(node.get_children())
            taken_positions = {c.position for c in children if c.position}
            if 'L' not in taken_positions:
                new_user_node.parent = node
                new_user_node.position = 'L'
                new_user_node.save()
                return node, 'L'
            if 'R' not in taken_positions:
                new_user_node.parent = node
                new_user_node.position = 'R'
                new_user_node.save()
                return node, 'R'
            # enqueue children for BFS
            queue.extend(children)

        # fallback: make it a root (if no slot found)
        new_user_node.parent = None
        new_user_node.position = None
        new_user_node.save()
        return None, None


    def left_child(self):
        return self.children.filter(position='L').first()

    def right_child(self):
        return self.children.filter(position='R').first()
