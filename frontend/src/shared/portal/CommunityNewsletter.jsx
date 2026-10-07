import Newsletter from '../../modules/publico/Newsletter.jsx';
import { usePortalRoute } from './PortalLayout.jsx';

export default function CommunityNewsletter() {
  const { base } = usePortalRoute();
  return <Newsletter portalBase={base} />;
}
