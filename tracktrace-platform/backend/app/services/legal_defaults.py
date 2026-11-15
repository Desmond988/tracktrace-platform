"""Default legal page text. PLACEHOLDER CONTENT ONLY - must be reviewed and replaced by the company's legal
representative before launch. Not legal advice. Edit through the admin API/UI (stored in legal_pages).

Only English and French are pre-written here (the two languages most likely to have an actual legal reviewer
on staff). Any other supported language falls back to English on the public site (see app.services.i18n)
until a staff member adds a real translation through the Legal admin page."""

REVIEW_NOTE = {
    "en": "This is placeholder text and has not been reviewed by a lawyer. It must be replaced or approved by  TracksLogistics's legal representative before publication.",
    "fr": "Ce texte est un modèle provisoire qui n'a pas été relu par un juriste. Il doit être remplacé ou approuvé par le représentant légal de  TracksLogistics avant publication.",
}

_P = {
    'privacy-policy': (
        {"en": 'Privacy Policy', "fr": 'Politique de confidentialité'},
        {"en": '## Who we are\n TracksLogistics, New York City, New York, United States, is responsible for the personal data described here. Contact:  trackslogistic0@gmail.com.\n\n## What we collect\nAccount details (name, email, phone), shipment and delivery details, messages you send us, and technical data needed to keep the service secure.\n\n## How we use it\nTo provide tracking and logistics services, respond to your requests, send shipment notifications you have enabled, and protect the platform against abuse.\n\n## Your rights\nYou may ask to access, correct or delete your data. Contact us using the details above.', "fr": "## Qui sommes-nous\n TracksLogistics, New York City, New York, United States, est responsable des données personnelles décrites ici. Contact :  trackslogistic0@gmail.com.\n\n## Ce que nous collectons\nLes informations de compte (nom, e-mail, téléphone), les détails d'expédition et de livraison, les messages que vous nous envoyez et les données techniques nécessaires à la sécurité du service.\n\n## Comment nous les utilisons\nPour fournir le suivi et les services logistiques, répondre à vos demandes, envoyer les notifications d'expédition que vous avez activées et protéger la plateforme contre les abus.\n\n## Vos droits\nVous pouvez demander l'accès, la correction ou la suppression de vos données en nous contactant aux coordonnées ci-dessus."},
    ),
    'terms-and-conditions': (
        {"en": 'Terms & Conditions', "fr": 'Conditions générales'},
        {"en": '## Using this website\nBy using this website you agree to these terms. Tracking information is provided for convenience and reflects the latest event recorded by our team.\n\n## Accounts\nYou are responsible for keeping your password confidential and for activity under your account.\n\n## Services\n Track and logistics services are provided under the agreement made with  TracksLogistics for each shipment. [COMPANY REGISTRATION]\n\n## Changes\nWe may update these terms. The date of the latest update will be shown here.', "fr": "## Utilisation du site\nEn utilisant ce site, vous acceptez ces conditions. Les informations de suivi sont fournies à titre indicatif et reflètent le dernier événement enregistré par notre équipe.\n\n## Comptes\nVous êtes responsable de la confidentialité de votre mot de passe et de l'activité de votre compte.\n\n## Services\nLes services de fret et de logistique sont fournis selon l'accord conclu avec  TracksLogistics pour chaque expédition. [COMPANY REGISTRATION]\n\n## Modifications\nNous pouvons mettre à jour ces conditions. La date de la dernière mise à jour sera indiquée ici."},
    ),
    'cookie-policy': (
        {"en": 'Cookie Policy', "fr": 'Politique relative aux cookies'},
        {"en": '## What we use\nThis website uses only cookies that are necessary to keep you signed in and to protect your session against forgery. We do not use advertising cookies.\n\n## Your choices\nYou can block cookies in your browser, but signing in will not work without them.', "fr": "## Ce que nous utilisons\nCe site utilise uniquement les cookies nécessaires pour maintenir votre connexion et protéger votre session contre la falsification. Nous n'utilisons pas de cookies publicitaires.\n\n## Vos choix\nVous pouvez bloquer les cookies dans votre navigateur, mais la connexion ne fonctionnera pas sans eux."},
    ),
    'shipping-terms': (
        {"en": 'Shipping Terms', "fr": "Conditions d'expédition"},
        {"en": '## Booking and acceptance\nShipments are accepted subject to the details supplied by the sender being accurate and complete, including cargo description, weight and dimensions.\n\n## Prohibited and restricted goods\n TracksLogistics will publish the list of prohibited and restricted goods here.\n\n## Delivery estimates\nEstimated delivery dates are estimates, not guarantees, and may change because of customs, weather, capacity or other factors outside our control.', "fr": "## Réservation et acceptation\nLes expéditions sont acceptées sous réserve que les informations fournies par l'expéditeur soient exactes et complètes, y compris la description de la marchandise, son poids et ses dimensions.\n\n## Marchandises interdites et restreintes\n TracksLogistics publiera ici la liste des marchandises interdites et restreintes.\n\n## Estimations de livraison\nLes dates de livraison estimées sont des estimations et non des garanties ; elles peuvent changer en raison de la douane, de la météo, des capacités ou d'autres facteurs indépendants de notre volonté."},
    ),
    'cargo-liability': (
        {"en": 'Cargo Liability', "fr": 'Responsabilité du transporteur'},
        {"en": '## Liability\nThe limits and conditions of liability for loss or damage to cargo depend on the mode of transport and the applicable law or convention.  TracksLogistics will state them here.\n\n## Claims\nReport loss or damage as soon as possible and keep the packaging and photographs. Contact  trackslogistic0@gmail.com.', "fr": "## Responsabilité\nLes limites et conditions de responsabilité en cas de perte ou de dommage dépendent du mode de transport et de la loi ou de la convention applicable.  TracksLogistics les indiquera ici.\n\n## Réclamations\nSignalez toute perte ou tout dommage dès que possible et conservez l'emballage et les photographies. Contactez  trackslogistic0@gmail.com."},
    ),
    'disclaimer': (
        {"en": 'Disclaimer', "fr": 'Avertissement'},
        {"en": '## Information on this site\nWe work to keep the information on this website accurate and current, but we do not guarantee that it is complete or error-free. Tracking data reflects events recorded by our team and its partners.', "fr": "## Informations sur ce site\nNous nous efforçons de maintenir les informations de ce site exactes et à jour, mais nous ne garantissons pas qu'elles soient complètes ou exemptes d'erreurs. Les données de suivi reflètent les événements enregistrés par notre équipe et ses partenaires."},
    ),
    'accessibility': (
        {"en": 'Accessibility', "fr": 'Accessibilité'},
        {"en": '## Our aim\nWe want this website to be usable by everyone, including people using keyboards and screen readers. If you find a barrier, tell us at  trackslogistic0@gmail.com and we will work with you to fix it.\n\n## Status\nAn accessibility conformance statement will be added here once  TracksLogistics has completed a formal review.', "fr": "## Notre objectif\nNous voulons que ce site soit utilisable par tous, y compris les personnes utilisant un clavier ou un lecteur d'écran. Si vous rencontrez un obstacle, écrivez-nous à  trackslogistic0@gmail.com et nous chercherons une solution avec vous.\n\n## État\nUne déclaration de conformité sera ajoutée ici lorsque  TracksLogistics aura réalisé un examen formel."},
    ),
    'data-protection': (
        {"en": 'Data Protection', "fr": 'Protection des données'},
        {"en": '## Security\nPasswords are stored using a one-way hash. Access to shipment data is limited to the customer it belongs to and authorised staff.\n\n## Retention\n TracksLogistics will state how long shipment, account and message data is kept.\n\n## Requests and complaints\nTo exercise your data rights, contact  trackslogistic0@gmail.com. The applicable data protection authority is [DATA PROTECTION AUTHORITY].', "fr": "## Sécurité\nLes mots de passe sont stockés sous forme de hachage à sens unique. L'accès aux données d'expédition est limité au client concerné et au personnel autorisé.\n\n## Conservation\n TracksLogistics indiquera combien de temps les données d'expédition, de compte et de messages sont conservées.\n\n## Demandes et réclamations\nPour exercer vos droits, contactez  trackslogistic0@gmail.com. L'autorité de protection des données compétente est [DATA PROTECTION AUTHORITY]."},
    ),
}

SLUGS = list(_P.keys())


def default_page(slug: str) -> dict | None:
    if slug not in _P:
        return None
    title, body = _P[slug]
    return {"slug": slug, "title": title, "body": body, "legally_reviewed": False, "review_note": REVIEW_NOTE}
