import React from "react";
import { Link } from "react-router-dom";

/**
 * Breadcrumbs navigation component.
 * @param {Array<{ label: string, to?: string, icon?: React.ReactNode }>} routes
 */
const Breadcrumbs = ({ routes }) => {
  return (
    <div className="breadcrumbs text-sm mb-6">
      <ul>
        {routes.map((route, idx) => (
          <li key={idx}>
            {route.to ? (
              <Link to={route.to} className="inline-flex items-center gap-2">
                {route.icon}
                {route.label}
              </Link>
            ) : (
              <span className="inline-flex items-center gap-2">
                {route.icon}
                {route.label}
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Breadcrumbs;
