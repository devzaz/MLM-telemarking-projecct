from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import MLMNode

def calculate_binary_bonus(node, amount):
    # placeholder: implement rules for matching
    # e.g., find left & right volumes up to n levels and compute match
    pass




# mlm/signals.py
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import MLMNode

User = get_user_model()

@receiver(post_save, sender=User)
def create_and_place_mlm_node(sender, instance, created, **kwargs):
    """
    When a new User is created, create an MLMNode for them and auto-place them
    if the signup flow supplied a referral code. The signup view should attach
    instance._mlm_referral_code = '<REF>' before saving the user instance.
    """
    if not created:
        return

    try:
        # create the MLMNode record if not exists (inactive by default)
        node, node_created = MLMNode.objects.get_or_create(user=instance, defaults={'active': False})
    except Exception as e:
        # fail-safe: log and return (avoid crashing user creation)
        import logging
        logging.getLogger('mlm').exception("Failed to create/get MLMNode for user %s: %s", instance.pk, e)
        return

    # If the signup view attached a referral code to the user instance, use it.
    ref_code = getattr(instance, '_mlm_referral_code', None)

    if ref_code:
        try:
            # find the referrer user by referral_code on User
            ref_user = User.objects.get(referral_code=ref_code)
            # ensure ref_user has an MLMNode (create if missing)
            start_node, _ = MLMNode.objects.get_or_create(user=ref_user, defaults={'active': False})
            # place new node under start_node using auto_place
            MLMNode.auto_place(node, start_node=start_node)
        except User.DoesNotExist:
            # invalid ref code — fallback to placing without start_node
            MLMNode.auto_place(node)
        except Exception as e:
            import logging
            logging.getLogger('mlm').exception("Failed to auto-place MLMNode for user %s: %s", instance.pk, e)
            # fallback to placing without a start node
            try:
                MLMNode.auto_place(node)
            except Exception:
                pass
    else:
        # No referral provided — default placement (optional: keep users unplaced for admin)
        # If you prefer to let admin place manually, comment the next line out.
        MLMNode.auto_place(node)
