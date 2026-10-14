import Newsletter from '../../modules/publico/Newsletter.jsx';
import { usePortalRoute } from './PortalLayout.jsx';
import { Link } from 'react-router-dom';

export default function CommunityNewsletter() {
  const { base } = usePortalRoute();
  return <><p><Link className="text-link" to="/encuestas">Responde las encuestas de Enlaces Institucionales ITS</Link></p><Newsletter portalBase={base} /></>;
}
