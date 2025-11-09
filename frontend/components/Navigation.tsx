'use client';

import { usePathname, useRouter } from 'next/navigation';

export function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  
  const isActive = (path: string) => {
    if (path === '/') {
      return pathname === '/';
    }
    return pathname.startsWith(path);
  };
  
  const navItems = [
    { name: 'Home', path: '/', icon: '🏠' },
    { name: 'Orders', path: '/orders', icon: '📦' },
    { name: 'Profile', path: '/profile', icon: '👤' }
  ];
  
  return (
    <nav className="bg-white shadow-sm mb-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex justify-center gap-2">
          {navItems.map((item) => (
            <button
              key={item.path}
              onClick={() => router.push(item.path)}
              className={`flex items-center gap-2 px-6 py-4 font-medium transition-all border-b-2 ${
                isActive(item.path)
                  ? 'border-[#C9915C] text-[#C9915C]'
                  : 'border-transparent text-gray-600 hover:text-[#C9915C]'
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.name}</span>
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}

