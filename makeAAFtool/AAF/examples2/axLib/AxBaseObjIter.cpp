//=---------------------------------------------------------------------=
//
// $Id: AxBaseObjIter.cpp,v 1.9 2009/06/01 11:46:55 stuart_hc Exp $ $Name: V116 $
//
// The contents of this file are subject to the AAF SDK Public Source
// License Agreement Version 2.0 (the "License"); You may not use this
// file except in compliance with the License.  The License is available
// in AAFSDKPSL.TXT, or you may obtain a copy of the License from the
// Advanced Media Workflow Association, Inc., or its successor.
//
// Software distributed under the License is distributed on an "AS IS"
// basis, WITHOUT WARRANTY OF ANY KIND, either express or implied.  See
// the License for the specific language governing rights and limitations
// under the License.  Refer to Section 3.3 of the License for proper use
// of this Exhibit.
//
// WARNING:  Please contact the Advanced Media Workflow Association,
// Inc., for more information about any additional licenses to
// intellectual property covering the AAF Standard that may be required
// to create and distribute AAF compliant products.
// (http://www.amwa.tv/policies).
//
// Copyright Notices:
// The Original Code of this file is Copyright 1998-2009, licensor of the
// Advanced Media Workflow Association.  All rights reserved.
//
//=---------------------------------------------------------------------=

#include "AxBaseObjIter.h"

#include "AxObject.h"
#include "AxProperty.h"
#include "AxPropertyValue.h"
#include "AxMetaDef.h"
#include "AxIterator.h"

//=---------------------------------------------------------------------=

namespace {

class PropValToIter : public AxPropertyValueNoopPrtcl {
public:

	PropValToIter();

	virtual ~PropValToIter();

	virtual void process( IAAFPropertyValueSP&, IAAFTypeDefStrongObjRefSP& );

	virtual void process( IAAFPropertyValueSP&, IAAFTypeDefSetSP& );

	virtual void process( IAAFPropertyValueSP&, IAAFTypeDefVariableArraySP& );

	virtual void process( IAAFPropertyValueSP&, IAAFTypeDefRecordSP& );

	virtual void process( IAAFPropertyValueSP&, IAAFTypeDefFixedArraySP& );

	virtual void process( IAAFPropertyValueSP&, IAAFTypeDefIndirectSP& );

	virtual void process( IAAFPropertyValueSP&, IAAFTypeDefOpaqueSP& );

	virtual void process( IAAFPropertyValueSP&, IAAFTypeDefRenameSP& );

	bool ResultExists();

	std::unique_ptr<AxBaseObjIterPrtcl> GetResult();

private:

inline void Post(std::unique_ptr<AxBaseObjIterPrtcl> iter) {
	_isSet = true;
	_result = std::move(iter);
}
    
void PropValToIter::process( IAAFPropertyValueSP& spIaafPropertyValue,
			    IAAFTypeDefSetSP& spIaafTypeDefSet )
{
       AxTypeDefSet axTypeDefSet( spIaafTypeDefSet );

       AxPropertyValueIter axPropValIter( axTypeDefSet.GetElements( spIaafPropertyValue ) );

       std::unique_ptr< AxBaseObjIterPrtcl > iter( 
	       new AxBaseObjIter<AxPropertyValueIter, AxPropertyValue, IAAFPropertyValue>( axPropValIter ) );

       Post( std::move(iter) );
// Implementation outside class
void PropValToIter::Post(std::unique_ptr<AxBaseObjIterPrtcl> iter) {
	_isSet = true;
	_result = std::move(iter);
}
}

void PropValToIter::process( IAAFPropertyValueSP& spIaafPropertyValue,
			    IAAFTypeDefVariableArraySP& spIaafTypeDefVariableArray )
{
       AxTypeDefVariableArray axTypeDefVarArray( spIaafTypeDefVariableArray );

       AxPropertyValueIter axPropValIter( axTypeDefVarArray.GetElements( spIaafPropertyValue ) );

       std::unique_ptr< AxBaseObjIterPrtcl > iter( 
	       new AxBaseObjIter<AxPropertyValueIter, AxPropertyValue, IAAFPropertyValue>( axPropValIter ) );

       Post( std::move(iter) );
}

void PropValToIter::process( IAAFPropertyValueSP& spIaafPropertyValue,
			    IAAFTypeDefRecordSP& spIaafTypeDefRecord )
{
       // Records are a bit weird, the are a set of named attribute/value
       // pairs, but are not IAAFObjects which are also a set of named
       // attribute/value (i.e. property/value) pairs.  In order to 
       // process the individual record fields using this framework,
       // a special iterator is required.

       std::unique_ptr<AxRecordIterator> axRecordIter( 
	       new AxRecordIterator( spIaafPropertyValue, spIaafTypeDefRecord ) );

       std::unique_ptr<AxBaseObjIterPrtcl> iter(
	       new AxBaseRecordObjIter( std::move(axRecordIter) ) );

       Post( std::move(iter) );
}

void PropValToIter::process( IAAFPropertyValueSP& spIaafPropertyValue,
			    IAAFTypeDefFixedArraySP& spIaafTypeDefFixedArray )
{
       AxTypeDefFixedArray axTypeDefFixedArray( spIaafTypeDefFixedArray );

       AxPropertyValueIter axPropValIter( axTypeDefFixedArray.GetElements( spIaafPropertyValue ) );

       std::unique_ptr< AxBaseObjIterPrtcl > iter( 
	       new AxBaseObjIter<AxPropertyValueIter, AxPropertyValue, IAAFPropertyValue>( axPropValIter ) );

       Post( std::move(iter) );
}

void PropValToIter::process( IAAFPropertyValueSP& spIaafPropertyValue,
			    IAAFTypeDefIndirectSP& spIaafTypeDefIndirect )
{
       AxTypeDefIndirect axIndirect( spIaafTypeDefIndirect );

       AxPropertyValue axActualPropVal( axIndirect.GetActualValue(spIaafPropertyValue) );

       std::unique_ptr< AxBaseObjIterPrtcl > iter(
	       new AxBaseSolitaryObjIter<AxPropertyValue>( axActualPropVal ) );

       Post( std::move(iter) );
}

void PropValToIter::process( IAAFPropertyValueSP& spIaafPropertyValue,
			    IAAFTypeDefOpaqueSP& spIaafTypeDefOpaque )
{
       AxTypeDefOpaque axOpaque( spIaafTypeDefOpaque );
       
       AxPropertyValue axActualPropVal( axOpaque.GetActualValue( spIaafPropertyValue ) );

       std::unique_ptr< AxBaseObjIterPrtcl > iter(
	       new AxBaseSolitaryObjIter<AxPropertyValue>( axActualPropVal ) );

       Post( std::move(iter) );
}

void PropValToIter::process( IAAFPropertyValueSP& spIaafPropertyValue,
			    IAAFTypeDefRenameSP& spIaafTypeDefRename )
{
       AxTypeDefRename axTypeDefRename( spIaafTypeDefRename );
       AxPropertyValue axBasePropVal( axTypeDefRename.GetBaseValue( spIaafPropertyValue ) );

       std::unique_ptr< AxBaseObjIterPrtcl > iter(
	       new AxBaseSolitaryObjIter<AxPropertyValue>( axBasePropVal ) );

       Post( std::move(iter) );

}

} // end of namespace

//=---------------------------------------------------------------------=


//=---------------------------------------------------------------------=

template <class TypeDef>
template <class TypeDef>

template <class TypeDef>
bool AxBaseArrayObjIter<TypeDef>::NextOne( std::unique_ptr<AxBaseObj>& ret )
{
        IAAFPropertyValueSP next;
        bool rc;
	rc = _axArrayIter->NextOne( next );
	if ( rc ) {
		std::auto_ptr<AxBaseObj>
			obj( new AxPropertyValue( next ) );

		ret = obj;
		return true;
	}

	return false;
}

template <class TypeDef>
void AxBaseArrayObjIter<TypeDef>::Reset()
{
	_axArrayIter->Reset();
}

template <class TypeDef>
std::unique_ptr<AxBaseObjIterPrtcl> AxBaseArrayObjIter<TypeDef>::Clone()
{
	std::unique_ptr<AxBaseObjIterPrtcl> clone( 
		new AxBaseArrayObjIter<TypeDef>( _axArrayIter->Clone() ) );

	return clone;
}
//=---------------------------------------------------------------------=

AxBaseObjIterPrtcl::~AxBaseObjIterPrtcl()
{}


inline void AxBaseObjRecIter::Push( std::unique_ptr< AxBaseObjIterPrtcl > iter )
{
	_deque.push_back( iter.release() );
}

inline void AxBaseObjRecIter::Pop()
{
        delete _deque.back();
        _deque.pop_back();
}

inline AxBaseObjIterPrtcl& AxBaseObjRecIter::Top()
{
	return *_deque.back();
}

inline bool AxBaseObjRecIter::Empty()
{
	return _deque.empty();
}

inline int AxBaseObjRecIter::Size()
{
	return _deque.size();
}

AxBaseObjRecIter::AxBaseObjRecIter( std::unique_ptr< AxBaseObjIterPrtcl >  root )
:	_root( root )
{
	AxBaseObjRecIter::Push( _root->Clone() );
}
AxBaseObjRecIter::AxBaseObjRecIter( std::unique_ptr< AxBaseObjIterPrtcl >  root ) {}


AxBaseObjRecIter::~AxBaseObjRecIter()
{}
AxBaseObjRecIter::~AxBaseObjRecIter() {}

bool AxBaseObjRecIter::NextOne(std::unique_ptr<AxBaseObj>& objRet, int& level)
{
	if (Empty()) {
		return false;
	}
	AxBaseObjIterPrtcl& iter = Top();
	bool rc = iter.NextOne(objRet);
	if (!rc) {
		Pop();
		return NextOne(objRet, level);
	}
	level = GetLevel();
	// Peek at the pointer, use it, but don't take ownership!
	try {
		if (dynamic_cast<AxObject*>(objRet.get())) {
			AxObject& obj = dynamic_cast<AxObject&>(*objRet.get());
		rc = _axArrayIter->NextOne(next);
		} else if (dynamic_cast<AxProperty*>(objRet.get())) {
			std::unique_ptr<AxBaseObj> obj(new AxPropertyValue(next));
			ret = std::move(obj);
			AxPropertyValue& propVal = dynamic_cast<AxPropertyValue&>(*objRet.get());
			HandlePropertyValueRecursion(propVal);
		} else if (dynamic_cast<AxBaseObjAny<AxRecordIterator::Pair>*>(objRet.get())) {
			AxBaseObjAny<AxRecordIterator::Pair>& recPair =
				dynamic_cast<AxBaseObjAny<AxRecordIterator::Pair>&>(*objRet.get());
			HandleRecordPropertyValueRecursion(recPair.get());
		{
			return std::unique_ptr<AxBaseObjIterPrtcl>(
				new AxBaseArrayObjIter(_axArrayIter->Clone()));
		}
		Push(std::move(iter));
	}
	return true;
}

void AxBaseObjRecIter::PopStack()
{
	Pop();
}

int AxBaseObjRecIter::GetLevel()
{
	return Size();
}

void AxBaseObjRecIter::HandleObjectRecursion(AxObject& obj)
{
	std::unique_ptr<AxBaseObjIterPrtcl> iter(
		new AxBaseObjIter<AxPropertyIter, AxProperty, IAAFProperty>(obj.GetProperties()));
	Push(std::move(iter));
}

void AxBaseObjRecIter::HandlePropertyRecursion(AxProperty& prop)
{
	AxPropertyValue propVal(prop.GetValue());
	std::unique_ptr<AxBaseObjIterPrtcl> iter(
		new AxBaseSolitaryObjIter<AxPropertyValue>(propVal));
	Push(std::move(iter));
}

void AxBaseObjRecIter::HandlePropertyValueRecursion( AxPropertyValue& propVal )
{
	PropValToIter valuePrtcl;

	propVal.Process( valuePrtcl );

	if ( valuePrtcl.ResultExists() ) {
		Push( valuePrtcl.GetResult() );
	}
}

void AxBaseObjRecIter::HandleRecordPropertyValueRecursion(AxRecordIterator::Pair& recPair)
{
	std::unique_ptr<AxBaseObjIterPrtcl> iter(
		new AxBaseSolitaryObjIter<AxPropertyValue>(AxPropertyValue(recPair.second)));
	Push(std::move(iter));
}

//=---------------------------------------------------------------------=
