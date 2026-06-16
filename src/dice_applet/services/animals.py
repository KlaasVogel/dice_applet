import secrets

ANIMAL_NAMES = [
    "Albatross",
    "Axolotl",
    "Badger",
    "Barracuda",
    "Bison",
    "Blobfish",
    "Capybara",
    "Chameleon",
    "Cheetah",
    "Chinchilla",
    "Chipmunk",
    "Condor",
    "Coyote",
    "Dingo",
    "Dolphin",
    "Echidna",
    "Elephant",
    "Flamingo",
    "Fox",
    "Gecko",
    "Giraffe",
    "Gorilla",
    "Hamster",
    "Hedgehog",
    "Hyena",
    "Iguana",
    "Jaguar",
    "Jellyfish",
    "Kangaroo",
    "Kiwi",
    "Koala",
    "Lemur",
    "Leopard",
    "Llama",
    "Lynx",
    "Manatee",
    "Meerkat",
    "Mongoose",
    "Narwhal",
    "Numbat",
    "Ocelot",
    "Octopus",
    "Okapi",
    "Orca",
    "Ostrich",
    "Otter",
    "Pangolin",
    "Parrot",
    "Porcupine",
    "Quokka",
    "Raccoon",
    "Rhino",
    "Salamander",
    "Sloth",
    "Tapir",
    "Tarantula",
    "Toucan",
    "Walrus",
    "Wombat",
    "Zebrafish",
]

SAFE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no ambiguous O/0/I/1


def generate_personal_code() -> str:
    """Generate an 8-char uppercase alphanumeric personal code."""
    return "".join(secrets.choice(SAFE_CHARS) for _ in range(8))


def generate_join_code() -> str:
    """Generate a 5-char uppercase alphanumeric classroom join code."""
    return "".join(secrets.choice(SAFE_CHARS) for _ in range(5))
