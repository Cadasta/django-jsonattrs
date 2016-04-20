from .factories import (
    OrganizationFactory, ProjectFactory, PartyFactory, ParcelFactory
)


def create_fixtures():
    res = {}

    for iorg in range(1, 4):
        org = OrganizationFactory.create(name='Organization #{}'.format(iorg))
        res['org{}'.format(iorg)] = org

        for iprj in range(1, 4):
            proj = ProjectFactory.create(
                name='Project #{}.{}'.format(iorg, iprj),
                organization=org
            )
            res['proj{}{}'.format(iorg, iprj)] = proj

            for ient in range(1, 6):
                parcel = ParcelFactory.create(
                    address='Parcel #{}.{}.{}'.format(iorg, iprj, ient),
                    project=proj
                )
                res['parcel{}{}{}'.format(iorg, iprj, ient)] = parcel

                party = PartyFactory.create(
                    name='Party #{}.{}.{}'.format(iorg, iprj, ient),
                    project=proj
                )
                res['party{}{}{}'.format(iorg, iprj, ient)] = party
