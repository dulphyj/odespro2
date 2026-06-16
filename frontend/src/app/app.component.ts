import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { MenubarModule } from 'primeng/menubar';
import { MenuItem } from 'primeng/api';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, MenubarModule],
  template: `
    <p-menubar [model]="items">
      <ng-template pTemplate="start">
        <span style="font-weight:bold;font-size:1.25rem;margin-left:0.5rem">DocApp</span>
      </ng-template>
    </p-menubar>
    <div style="padding:1.5rem;max-width:1200px;margin:0 auto">
      <router-outlet />
    </div>
  `,
})
export class AppComponent {
  items: MenuItem[] = [
    { label: 'Subir', icon: 'pi pi-upload', routerLink: '/upload' },
    { label: 'Documentos', icon: 'pi pi-file', routerLink: '/documents' },
  ];
}
